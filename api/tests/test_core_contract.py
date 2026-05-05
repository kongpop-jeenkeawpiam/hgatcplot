import unittest
from pathlib import Path

from app.parser import parse_tabular_text
from app.registry import get_module, list_modules
from app.renderers import render_plot


class ParserContractTests(unittest.TestCase):
    def test_parses_tab_delimited_text_and_reports_preview(self):
        parsed = parse_tabular_text("gene\tlog2FC\tpvalue\nA\t1.2\t0.01\nB\t-2.4\t0.2\n")

        self.assertEqual(parsed.headers, ["gene", "log2FC", "pvalue"])
        self.assertEqual(parsed.row_count, 2)
        self.assertEqual(parsed.column_count, 3)
        self.assertEqual(parsed.preview_rows[0]["gene"], "A")
        self.assertEqual(parsed.errors, [])

    def test_warns_for_comma_decimal_and_special_characters(self):
        parsed = parse_tabular_text("gene\tvalue\nA(1)\t3,14\n")

        self.assertEqual(parsed.errors, [])
        self.assertTrue(any("decimal point" in warning for warning in parsed.warnings))
        self.assertTrue(any("special characters" in warning for warning in parsed.warnings))


class ModuleRegistryContractTests(unittest.TestCase):
    def test_registry_exposes_seed_modules_grouped_by_category(self):
        modules = list_modules()
        slugs = {module.slug for module in modules}

        self.assertGreaterEqual(len(modules), 12)
        self.assertIn("volcano", slugs)
        self.assertIn("heatmap", slugs)
        self.assertIn("km-survival", slugs)
        self.assertIn("pca", slugs)
        self.assertTrue(all(module.export_formats == ["png", "tiff", "svg", "pdf"] for module in modules))

    def test_module_manifest_contains_demo_data_and_required_columns(self):
        module = get_module("volcano")

        self.assertEqual(module.category, "Transcriptome")
        self.assertEqual(module.required_columns, ["gene", "log2FC", "pvalue"])
        self.assertIn("log2FC", module.demo_data)


class RendererContractTests(unittest.TestCase):
    def test_each_seed_module_renders_all_export_artifacts(self):
        output_root = Path(__file__).resolve().parents[1] / "storage" / "test-renders"
        output_root.mkdir(parents=True, exist_ok=True)

        for module in list_modules():
            with self.subTest(module=module.slug):
                parsed = parse_tabular_text(module.demo_data)
                result = render_plot(module.slug, parsed, module.default_options, output_root / module.slug)

                self.assertEqual(result.status, "succeeded")
                self.assertEqual(set(result.artifacts), {"png", "tiff", "svg", "pdf"})
                for artifact in result.artifacts.values():
                    path = Path(artifact)
                    self.assertTrue(path.exists())
                    self.assertGreater(path.stat().st_size, 50)


if __name__ == "__main__":
    unittest.main()
