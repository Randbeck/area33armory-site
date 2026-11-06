"""Ensure Pages deployment remains manual and inactive on development branches.

Publishing requires separate owner approval and selected, audited public
release files. Tests do not request GitHub Pages deployment.
"""
from __future__ import annotations

from pathlib import Path
import unittest


class GithubPagesManualWorkflowTests(unittest.TestCase):
    def test_only_inactive_workflow_template_present(self):
        root=Path(__file__).resolve().parents[1]
        example=root/"examples/area33-github-pages-manual-deploy-TEMPLATE.yml"
        self.assertTrue(example.is_file())
        self.assertFalse((root/".github/workflows/area33-github-pages-manual-deploy.yml").exists())
        text=example.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:",text)
        self.assertNotIn("\n  push:",text)
        self.assertIn("PUBLISH AREA33 APPROVED CATALOG",text)
        self.assertIn("ref: main",text)
        self.assertIn("ref: ${{ inputs.release_branch }}",text)
        self.assertIn("git -C candidate rev-parse HEAD",text)
        self.assertIn("scripts/verify_github_pages_candidate.py",text)
        self.assertIn("path: candidate/site",text)
        self.assertIn("actions/upload-pages-artifact@",text)
        self.assertIn("actions/deploy-pages@",text)
        self.assertIn("needs: verify-public-candidate",text)
        self.assertIn("name: github-pages",text)

    def test_existing_dev_ci_has_no_production_pages_deployer(self):
        root=Path(__file__).resolve().parents[1]
        workflows=(root/".github/workflows").glob("*.yml")
        for file in workflows:
            text=file.read_text(encoding="utf-8")
            self.assertNotIn("actions/deploy-pages@",text)
            self.assertNotIn("pages: write",text)


if __name__=="__main__":
    unittest.main()
