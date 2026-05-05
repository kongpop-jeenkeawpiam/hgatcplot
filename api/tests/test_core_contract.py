import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app.parser import parse_tabular_text
from app.registry import get_module, list_modules
from app.r_engine import RCheckResult, check_r_engine, run_r_renderer
from app.renderers import render_plot


TEST_TMP_ROOT = Path(
    os.environ.get(
        "HGATCPLOT_TEST_TMP_ROOT",
        str(Path(__file__).resolve().parents[1] / "storage" / "test-tmp"),
    )
)


def temporary_directory() -> tempfile.TemporaryDirectory:
    TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(dir=TEST_TMP_ROOT, ignore_cleanup_errors=True)


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
    def test_registry_exposes_all_srplot_templates_with_unique_contracts(self):
        modules = list_modules()
        slugs = {module.slug for module in modules}
        source_urls = {module.source_url for module in modules}

        self.assertEqual(len(modules), 125)
        self.assertEqual(len(slugs), 125)
        self.assertEqual(len(source_urls), 125)
        self.assertIn("volcano", slugs)
        self.assertIn("heatmap", slugs)
        self.assertIn("motif-logo", slugs)
        self.assertIn("maf-oncoplot", slugs)
        self.assertIn("km-survival", slugs)
        self.assertIn("pca", slugs)
        self.assertTrue(all(module.export_formats == ["png", "tiff", "svg", "pdf"] for module in modules))
        self.assertTrue(all(module.source_url.startswith("https://bioinformatics.com.cn/en") for module in modules))
        self.assertTrue(all(module.engine in {"python", "r"} for module in modules))
        self.assertTrue(all(module.renderer_family for module in modules))
        self.assertGreaterEqual(sum(1 for module in modules if module.engine == "r"), 25)
        valid_visual_kinds = {
            "pie", "bar", "line", "scatter", "distribution", "density", "heatmap",
            "matrix", "bubble", "enrichment", "forest", "survival", "roc", "pca",
            "set", "network", "hierarchy", "funnel", "genome", "epigenome",
            "pathway", "maf", "sequence", "calendar", "polar", "wordcloud",
            "correlation", "qq", "radar", "area", "dual-axis", "dumbbell",
            "volcano",
        }
        valid_quality = {"practical", "family", "r-only"}
        self.assertTrue(all(module.visual_kind in valid_visual_kinds for module in modules))
        self.assertTrue(all(module.renderer_quality in valid_quality for module in modules))
        self.assertTrue(all(module.option_groups for module in modules))
        self.assertEqual(get_module("volcano").renderer_quality, "practical")
        self.assertEqual(get_module("heatmap").renderer_quality, "practical")
        self.assertEqual(get_module("bubble").renderer_quality, "practical")
        self.assertEqual(get_module("violin").renderer_quality, "practical")
        self.assertEqual(get_module("pie").renderer_quality, "practical")
        self.assertEqual(get_module("line").renderer_quality, "practical")
        self.assertEqual(get_module("scatter").renderer_quality, "practical")
        self.assertEqual(get_module("pca").renderer_quality, "practical")
        self.assertEqual(get_module("roc").renderer_quality, "practical")
        self.assertEqual(get_module("km-survival").renderer_quality, "practical")
        self.assertEqual(get_module("forest-plot").renderer_quality, "practical")

    def test_module_manifest_contains_demo_data_and_required_columns(self):
        module = get_module("volcano")

        self.assertEqual(module.category, "Transcriptome")
        self.assertEqual(module.required_columns, ["gene", "log2FC", "pvalue"])
        self.assertIn("log2FC", module.demo_data)
        self.assertIn("volcano", module.aliases)

    def test_every_module_has_demo_data_options_and_exports(self):
        for module in list_modules():
            with self.subTest(module=module.slug):
                parsed = parse_tabular_text(module.demo_data)
                self.assertEqual(parsed.errors, [])
                self.assertGreater(parsed.row_count, 0)
                self.assertTrue(set(module.required_columns).issubset(parsed.headers))
                self.assertTrue(module.default_options)
                self.assertTrue(module.option_fields)


class RendererContractTests(unittest.TestCase):
    def test_non_bar_visual_kinds_do_not_route_to_generic_bar_renderer(self):
        import app.renderers as renderers

        bar_like = {"bar", "errorbar", "stacked-bar"}
        for module in list_modules():
            if module.engine == "r":
                continue
            with self.subTest(module=module.slug):
                renderer = renderers._select_renderer(module)
                if module.renderer_family not in bar_like and module.visual_kind != "bar":
                    self.assertIsNot(renderer, renderers._render_generic)

    def test_each_module_demo_renders_all_export_artifacts(self):
        r_available = check_r_engine().available
        skipped_r_modules = []

        with temporary_directory() as tmp:
            output_root = Path(tmp)
            for module in list_modules():
                if module.engine == "r" and not r_available:
                    skipped_r_modules.append(module.slug)
                    continue
                with self.subTest(module=module.slug):
                    parsed = parse_tabular_text(module.demo_data)
                    result = render_plot(module.slug, parsed, module.default_options, output_root / module.slug)

                    self.assertEqual(result.status, "succeeded", result.errors)
                    self.assertEqual(set(result.artifacts), {"png", "tiff", "svg", "pdf"})
                    for artifact in result.artifacts.values():
                        path = Path(artifact)
                        self.assertTrue(path.exists())
                        self.assertGreater(path.stat().st_size, 50)

        if skipped_r_modules:
            self.skipTest(f"R is unavailable; skipped {len(skipped_r_modules)} R module render checks.")


class REngineContractTests(unittest.TestCase):
    def test_missing_configured_r_executable_reports_clear_error(self):
        with mock.patch.dict(os.environ, {"HGATCPLOT_RSCRIPT": "Z:/missing/R.exe"}):
            status = check_r_engine()

        self.assertFalse(status.available)
        self.assertTrue(any("HGATCPLOT_RSCRIPT" in error for error in status.errors))

    def test_failed_r_package_load_reports_error(self):
        if not check_r_engine().available:
            self.skipTest("R is unavailable in this environment.")

        status = check_r_engine(["HGATCplotMissingPackageForTest"])

        self.assertFalse(status.available)
        self.assertTrue(status.errors)

    def test_r_render_timeout_is_reported(self):
        module = get_module("motif-logo")
        parsed = parse_tabular_text(module.demo_data)
        fake_status = RCheckResult(True, "R.exe", "R version test", [])

        with temporary_directory() as tmp:
            with mock.patch("app.r_engine.check_r_engine", return_value=fake_status):
                with mock.patch("app.r_engine.subprocess.run", side_effect=subprocess.TimeoutExpired("R", 1)):
                    result = run_r_renderer(module, parsed, module.default_options, Path(tmp))

        self.assertEqual(result.status, "failed")
        self.assertTrue(any("timed out" in error for error in result.errors))

    def test_r_module_invalid_input_fails_before_render(self):
        parsed = parse_tabular_text("wrong\tcolumns\nA\t1\n")
        with temporary_directory() as tmp:
            result = render_plot("motif-logo", parsed, {}, Path(tmp))

        self.assertEqual(result.status, "failed")
        self.assertTrue(any("Missing required column" in error for error in result.errors))

    def test_r_module_generates_artifacts_when_r_is_available(self):
        if not check_r_engine().available:
            self.skipTest("R is unavailable in this environment.")

        module = get_module("motif-logo")
        parsed = parse_tabular_text(module.demo_data)
        with temporary_directory() as tmp:
            result = render_plot(module.slug, parsed, module.default_options, Path(tmp))

            self.assertEqual(result.status, "succeeded", result.errors)
            self.assertEqual(set(result.artifacts), {"png", "tiff", "svg", "pdf"})


if __name__ == "__main__":
    unittest.main()
