"""
UX AI Audit System - Main Entry Point
Orchestrates all analysis modules (A through E)
"""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import (
    validate_config,
    SCREENSHOTS_DIR,
    REPORTS_DIR,
    LOG_FILE,
    OPENAI_MODEL
)
from src.utils.playwright_helper import PlaywrightHelper
from src.utils.image_processor import ImageProcessor
from src.modules.module_a import ModuleA
from src.modules.module_b import ModuleB
from src.modules.module_c import ModuleC
from src.modules.module_d import ModuleD
from src.modules.module_e import ModuleE
from src.utils.deepseek_helper import is_deepseek_available


class UXAuditOrchestrator:
    """Main orchestrator for the UX AI Audit System"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the audit orchestrator

        Args:
            config: Input configuration with url, task, and persona
        """
        self.config = config
        self.url = config.get("url")
        self.task = config.get("task")
        self.persona = config.get("persona", "Elderly User")
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = SCREENSHOTS_DIR / self.session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)

        # Results from each module
        self.results = {
            "session_id": self.session_id,
            "config": config,
            "module_a_results": {},  # Visual Inspector
            "module_b_results": {},  # Behavioral Agent
            "module_c_results": {},  # Code Auditor
            "module_d_results": {},  # Sentiment Analyzer
            "module_e_results": {}   # Synthesizer
        }

    async def run_full_audit(self):
        """Run complete audit pipeline"""
        print(f"\n{'='*60}")
        print(f"UX AI AUDIT SYSTEM - Session {self.session_id}")
        print(f"{'='*60}")
        print(f"URL: {self.url}")
        print(f"Task: {self.task}")
        print(f"Persona: {self.persona}")
        print(f"{'='*60}\n")

        try:
            # Stage 1: Capture baseline data
            print("\n[STAGE 1] Capturing baseline data...")
            await self._capture_baseline()

            # Stage 2: Module A - Visual Analysis
            print("\n[STAGE 2] Module A: Visual Inspector")
            await self._run_module_a()

            # Stage 3: Module B - Behavioral Simulation
            await self._run_module_b()

            # Stage 4: Module C - Code Auditing (Accessibility)
            await self._run_module_c()

            # Stage 5: Module D - Sentiment Analysis
            await self._run_module_d()

            # Stage 6: Module E - Synthesis
            await self._run_module_e()

            # Save results
            self._save_results()

            print(f"\n{'='*60}")
            print(f"AUDIT COMPLETE")
            print(f"Session directory: {self.session_dir}")
            print(f"{'='*60}\n")

        except Exception as e:
            print(f"\n[ERROR] Audit failed: {e}")
            raise

    async def _capture_baseline(self):
        """Capture baseline screenshot and DOM"""
        async with PlaywrightHelper(headless=False) as helper:
            print(f"  → Navigating to {self.url}...")
            success = await helper.navigate(self.url)

            if not success:
                raise Exception(f"Failed to navigate to {self.url}")

            # Take screenshot
            screenshot_path = self.session_dir / "baseline_screenshot.png"
            print(f"  → Taking screenshot...")
            await helper.take_screenshot(
                filename="baseline_screenshot.png",
                path=self.session_dir
            )

            # Add grid overlay
            print(f"  → Adding grid overlay...")
            processor = ImageProcessor()
            grid_screenshot = self.session_dir / "baseline_screenshot_grid.png"
            processor.add_grid_overlay(screenshot_path, grid_screenshot)

            # Get DOM
            print(f"  → Extracting DOM snapshot...")
            dom = await helper.get_dom_snapshot()
            dom_path = self.session_dir / "baseline_dom.html"
            dom_path.write_text(dom, encoding="utf-8")

            # Get accessibility tree
            print(f"  → Extracting accessibility tree...")
            a11y_tree = await helper.get_accessibility_tree()
            a11y_path = self.session_dir / "baseline_accessibility.json"
            a11y_path.write_text(json.dumps(a11y_tree, indent=2), encoding="utf-8")

            # Get simplified DOM
            print(f"  → Extracting simplified DOM...")
            simplified = await helper.get_simplified_dom()
            simplified_path = self.session_dir / "baseline_simplified.html"
            simplified_path.write_text(simplified, encoding="utf-8")

            print(f"  ✓ Baseline data captured")

            # Store paths in results
            self.results["baseline"] = {
                "screenshot": str(screenshot_path),
                "screenshot_grid": str(grid_screenshot),
                "dom": str(dom_path),
                "accessibility_tree": str(a11y_path),
                "simplified_dom": str(simplified_path)
            }

    async def _run_module_a(self):
        """Run Module A - Visual Inspector"""
        try:
            # Get screenshot with grid overlay
            grid_screenshot = self.session_dir / "baseline_screenshot_grid.png"

            if not grid_screenshot.exists():
                print("  ⚠ Grid screenshot not found, skipping Module A")
                return

            # Initialize Module A
            print(f"  → Initializing {OPENAI_MODEL} (OpenAI Vision)...")
            module_a = ModuleA()

            # Run analysis
            print(f"  → Analyzing UI with persona: {self.persona}...")
            result = module_a.analyze_screenshot(
                screenshot_path=grid_screenshot,
                persona_name=self.persona,
                session_dir=self.session_dir
            )

            # Store results
            self.results["module_a_results"] = {
                "total_issues": result["summary"]["total_issues"],
                "severity_breakdown": {
                    "critical": result["summary"]["critical"],
                    "high": result["summary"]["high"],
                    "medium": result["summary"]["medium"],
                    "low": result["summary"]["low"]
                },
                "overall_assessment": result["summary"]["overall_assessment"],
                "issues_file": str(self.session_dir / "module_a_visual_analysis.json")
            }

            # Print summary
            module_a.print_summary(result)

            print(f"  ✓ Module A complete")

        except Exception as e:
            print(f"  ✗ Module A failed: {e}")
            import traceback
            traceback.print_exc()
            self.results["module_a_results"] = {"error": str(e)}

    async def _run_module_b(self):
        """Run Module B - Behavioral Simulation"""
        try:
            print("\n[STAGE 3] Module B: Behavioral Agent")
            print(f"  → Инициализация поведенческого симулятора...")

            # Initialize Module B
            module_b = ModuleB(
                session_dir=self.session_dir,
                persona_key=self.persona,
                task=self.task,
                max_steps=self.config.get("max_steps", 15)
            )

            print(f"  → Запуск симуляции...")
            print(f"     Персона: {self.persona}")
            print(f"     Задача: {self.task}")
            print(f"     Макс. шагов: {self.config.get('max_steps', 15)}")

            # Run simulation
            result = await module_b.simulate_behavior(
                starting_url=self.url
            )

            # Store results
            self.results["module_b_results"] = {
                "total_steps": result["total_steps"],
                "task_status": result["task_status"],
                "termination_reason": result["termination_reason"],
                "behavioral_log_file": str(self.session_dir / "module_b_behavioral_log.json")
            }

            # Print summary
            module_b.print_summary(result)

            print(f"  ✓ Module B завершён")

        except Exception as e:
            print(f"  ✗ Module B завершился с ошибкой: {e}")
            import traceback
            traceback.print_exc()
            self.results["module_b_results"] = {"error": str(e)}

    async def _run_module_c(self):
        """Run Module C - Accessibility Auditor"""
        try:
            print("\n[STAGE 4] Module C: Accessibility Auditor")
            print(f"  → Инициализация сканера доступности...")

            module_c = ModuleC(
                session_dir=self.session_dir,
                persona_key=self.persona,
                wcag_level="AA"
            )

            # Check if Module B behavioral log exists for multi-page scanning
            behavioral_log = self.session_dir / "module_b_behavioral_log.json"

            if behavioral_log.exists():
                print(f"  → Мульти-страничное сканирование по логу Module B...")
                result = await module_c.scan_from_module_b_log(behavioral_log)
            else:
                print(f"  → Одностраничное сканирование {self.url}...")
                result = await module_c.scan_urls([self.url])

            # Store results
            self.results["module_c_results"] = {
                "total_issues": result["summary"]["total_issues"],
                "by_impact": result["summary"]["by_impact"],
                "wcag_level": result["wcag_level"],
                "pages_scanned": len(result["pages_scanned"]),
                "issues_file": str(self.session_dir / "module_c_accessibility_scan.json")
            }

            # Print summary
            module_c.print_summary(result)

            print(f"  ✓ Module C завершён")

        except Exception as e:
            print(f"  ✗ Module C завершился с ошибкой: {e}")
            import traceback
            traceback.print_exc()
            self.results["module_c_results"] = {"error": str(e)}

    async def _run_module_d(self):
        """Run Module D - Sentiment Analyzer"""
        try:
            print("\n[STAGE 5] Module D: Sentiment Analyzer")

            # Check if DeepSeek is configured
            if not is_deepseek_available():
                print("  ⚠ DeepSeek API не настроен, пропуск Module D")
                print("     Добавьте DEEPSEEK_API_KEY в .env для анализа настроений")
                self.results["module_d_results"] = {"skipped": "deepseek_not_configured"}
                return

            # Check if behavioral log exists
            behavioral_log = self.session_dir / "module_b_behavioral_log.json"

            if not behavioral_log.exists():
                print("  ⚠ Поведенческий лог не найден, пропуск Module D")
                self.results["module_d_results"] = {"skipped": "no_behavioral_log"}
                return

            print(f"  → Инициализация анализатора настроений...")

            # Check if deep analysis with reasoner is requested
            use_reasoner = self.config.get("use_reasoner", False)
            if use_reasoner:
                print(f"  -> Deep analysis mode (DeepSeek Reasoner)")

            module_d = ModuleD(
                session_dir=self.session_dir,
                persona_key=self.persona,
                use_reasoner=use_reasoner
            )

            print(f"  → Анализ {behavioral_log.name}...")
            result = await module_d.analyze_behavioral_log(behavioral_log)

            # Store results
            self.results["module_d_results"] = {
                "session_score": result["summary"]["session_score"],
                "trend": result["summary"]["trend"],
                "distribution": result["summary"]["distribution"],
                "pain_points_count": len(result["pain_points"]),
                "insights": result["insights"],
                "analysis_file": str(self.session_dir / "module_d_sentiment_analysis.json")
            }

            # Print summary
            module_d.print_summary(result)

            print(f"  ✓ Module D завершён")

        except Exception as e:
            print(f"  ✗ Module D завершился с ошибкой: {e}")
            import traceback
            traceback.print_exc()
            self.results["module_d_results"] = {"error": str(e)}

    async def _run_module_e(self):
        """Run Module E - Report Synthesizer"""
        try:
            print("\n[STAGE 6] Module E: Report Synthesizer")
            print(f"  -> Инициализация генератора отчетов...")

            # First save results so Module E can read them
            self._save_results()

            module_e = ModuleE(session_dir=self.session_dir)

            print(f"  -> Генерация отчета...")
            report = module_e.generate_report(audit_results=self.results)

            print(f"  -> Создание HTML отчета...")
            html_path = module_e.generate_html_report()

            # Store results
            self.results["module_e_results"] = {
                "overall_score": report["overall_score"]["overall"],
                "rating": report["overall_score"]["rating_label"],
                "issues_count": len(report.get("all_issues", [])),
                "recommendations_count": len(report.get("recommendations", [])),
                "json_report": str(self.session_dir / "module_e_final_report.json"),
                "html_report": str(html_path)
            }

            # Print summary
            module_e.print_summary(report)

            print(f"  [OK] Module E завершен")
            print(f"      HTML отчет: {html_path}")

        except Exception as e:
            print(f"  [X] Module E завершился с ошибкой: {e}")
            import traceback
            traceback.print_exc()
            self.results["module_e_results"] = {"error": str(e)}

    def _save_results(self):
        """Save audit results to JSON"""
        results_path = self.session_dir / "audit_results.json"
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"\n  ✓ Results saved to {results_path}")


async def main():
    """Main entry point"""
    # Validate configuration
    try:
        validate_config()
    except ValueError as e:
        print(f"\n[ERROR] {e}")
        print("\nPlease create a .env file based on .env.example and set your API keys.")
        return

    # Load input configuration
    # For now, use a default config - later this will be loaded from input.json
    config = {
        "url": "https://example.com",
        "task": "Find product 'Nike Air' and add to cart",
        "persona": "Elderly User"
    }

    # Check if input.json exists
    input_file = Path("input.json")
    if input_file.exists():
        print("Loading configuration from input.json...")
        with open(input_file, "r", encoding="utf-8") as f:
            config = json.load(f)

    # Run audit
    orchestrator = UXAuditOrchestrator(config)
    await orchestrator.run_full_audit()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Audit stopped by user")
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
