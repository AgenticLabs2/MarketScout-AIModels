import threading
import unittest
from unittest.mock import patch
from uuid import uuid4

from src.pipeline import pipeline


def _ok(data):
    return {"success": True, "data": data, "raw_response": "{}"}


class LangGraphPipelineTests(unittest.TestCase):
    def test_interrupt_resume_parallel_join_and_report(self):
        parallel_barrier = threading.Barrier(2)

        def market_data(_domain):
            parallel_barrier.wait(timeout=2)
            return _ok({"market_size_usd": 1.0, "CAGR": 0.1, "key_drivers": [], "sources": []})

        def competitors(_opportunity):
            parallel_barrier.wait(timeout=2)
            return _ok([])

        patches = (
            patch.object(pipeline, "run_company_research_agent", return_value=_ok({"name": "Acme"})),
            patch.object(
                pipeline,
                "run_industry_analysis_agent",
                return_value=_ok([
                    {"domain": "Health Tech", "score": 0.9, "rationale": "Fit", "sources": []}
                ]),
            ),
            patch.object(pipeline, "run_market_data_agent", side_effect=market_data),
            patch.object(pipeline, "run_competitive_landscape_agent", side_effect=competitors),
            patch.object(pipeline, "run_market_gap_analysis_agent", return_value=_ok([])),
            patch.object(pipeline, "run_opportunity_agent", return_value=_ok([])),
            patch.object(
                pipeline,
                "run_report_synthesis_agent",
                return_value=_ok({"pdf_content": b"%PDF-test", "report_title": "Acme"}),
            ),
        )

        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6]:
            thread_id = str(uuid4())
            paused = pipeline.run_linear_pipeline("Acme", thread_id=thread_id)
            self.assertEqual(paused["status"], "interrupted")
            self.assertEqual(paused["interrupt"]["kind"], "domain_selection")

            completed = pipeline.resume_pipeline(thread_id, 1)

        self.assertTrue(completed["success"])
        self.assertEqual(completed["status"], "completed")
        self.assertEqual(completed["data"]["selected_domain"], "Health Tech")
        self.assertEqual(completed["data"]["report_data"]["pdf_content_encoding"], "base64")


if __name__ == "__main__":
    unittest.main()
