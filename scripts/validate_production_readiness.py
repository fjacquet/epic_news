#!/usr/bin/env python3
"""
Production Readiness Validation Script

This script validates that the cooking crew is production-ready by checking:
1. All recipe files are in correct output directory
2. Task configuration enforces correct file paths
3. Tool muting is properly configured
4. File organization compliance
"""

import sys
from pathlib import Path
from typing import Any

import yaml


class ProductionReadinessValidator:
    """Validates production readiness of the cooking crew system."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.output_dir = self.project_root / "output" / "cooking"
        self.issues = []
        self.warnings = []
        self.successes = []

    def validate_file_organization(self) -> bool:
        """Check that the cooking output directory exists and holds recipe files."""
        print("🔍 Validating file organization...")

        # Check output directory exists and has files
        if not self.output_dir.exists():
            self.issues.append("❌ Output directory 'output/cooking/' does not exist")
            return False

        output_yaml_files = list(self.output_dir.glob("*.yaml"))

        if output_yaml_files:
            self.successes.append(f"✅ Found {len(output_yaml_files)} YAML files in correct output directory")
        else:
            self.warnings.append("⚠️ No YAML files found in output directory")

        return True

    def validate_task_configuration(self) -> bool:
        """Check that task configuration enforces correct file paths."""
        print("🔍 Validating task configuration...")

        tasks_config_path = (
            self.project_root / "src" / "epic_news" / "crews" / "cooking" / "config" / "tasks.yaml"
        )

        if not tasks_config_path.exists():
            self.issues.append("❌ Tasks configuration file not found")
            return False

        try:
            with open(tasks_config_path, encoding="utf-8") as f:
                tasks_config = yaml.safe_load(f)

            # Check YAML task configuration
            yaml_task = tasks_config.get("paprika_yaml_task", {})
            yaml_expected = yaml_task.get("expected_output", "")

            if "output/cooking/" in yaml_expected:
                self.successes.append("✅ YAML task specifies correct output directory")
            else:
                self.warnings.append("⚠️ YAML task should specify correct output directory")

            return True

        except Exception as e:
            self.issues.append(f"❌ Error reading task configuration: {str(e)}")
            return False

    def validate_tool_muting(self) -> bool:
        """Check that tool muting is properly configured."""
        print("🔍 Validating tool muting configuration...")

        cooking_crew_path = self.project_root / "src" / "epic_news" / "crews" / "cooking" / "cooking_crew.py"
        tool_logging_path = self.project_root / "src" / "epic_news" / "utils" / "tool_logging.py"

        if not cooking_crew_path.exists():
            self.issues.append("❌ Cooking crew file not found")
            return False

        if not tool_logging_path.exists():
            self.issues.append("❌ Tool logging utility not found")
            return False

        try:
            with open(cooking_crew_path, encoding="utf-8") as f:
                crew_content = f.read()

            if "apply_tool_silence()" in crew_content:
                self.successes.append("✅ Tool silencing is configured in cooking crew")
            else:
                self.warnings.append("⚠️ Tool silencing not found in cooking crew")

            if "configure_tool_logging" in crew_content:
                self.successes.append("✅ Tool logging configuration is available")
            else:
                self.warnings.append("⚠️ Tool logging configuration not imported")

            return True

        except Exception as e:
            self.issues.append(f"❌ Error reading cooking crew file: {str(e)}")
            return False

    def validate_gitignore(self) -> bool:
        """Check that .gitignore properly excludes output directory."""
        print("🔍 Validating .gitignore configuration...")

        gitignore_path = self.project_root / ".gitignore"

        if not gitignore_path.exists():
            self.warnings.append("⚠️ .gitignore file not found")
            return True

        try:
            with open(gitignore_path, encoding="utf-8") as f:
                gitignore_content = f.read()

            if "output/" in gitignore_content and not gitignore_content.count("# output/"):
                self.successes.append("✅ Output directory is properly excluded from git")
            else:
                self.warnings.append("⚠️ Output directory should be excluded from git")

            return True

        except Exception as e:
            self.warnings.append(f"⚠️ Error reading .gitignore: {str(e)}")
            return True

    def generate_report(self) -> dict[str, Any]:
        """Generate a comprehensive validation report."""
        total_checks = len(self.successes) + len(self.warnings) + len(self.issues)

        report = {
            "production_ready": len(self.issues) == 0,
            "total_checks": total_checks,
            "successes": len(self.successes),
            "warnings": len(self.warnings),
            "critical_issues": len(self.issues),
            "details": {
                "successes": self.successes,
                "warnings": self.warnings,
                "critical_issues": self.issues,
            },
            "recommendations": [],
        }

        if self.issues:
            report["recommendations"].append("🚨 Fix all critical issues before deploying to production")

        if self.warnings:
            report["recommendations"].append("⚠️ Address warnings to improve system robustness")

        if len(self.issues) == 0 and len(self.warnings) == 0:
            report["recommendations"].append("🎉 System is production ready!")

        return report

    def run_validation(self) -> bool:
        """Run all validation checks."""
        print("🚀 Starting Production Readiness Validation...\n")

        # Run all validation checks
        checks = [  # noqa: F841
            self.validate_file_organization(),
            self.validate_task_configuration(),
            self.validate_tool_muting(),
            self.validate_gitignore(),
        ]

        # Generate and display report
        report = self.generate_report()

        print("\n" + "=" * 60)
        print("📊 PRODUCTION READINESS REPORT")
        print("=" * 60)

        if report["production_ready"]:
            print("🎉 STATUS: PRODUCTION READY ✅")
        else:
            print("🚨 STATUS: NOT PRODUCTION READY ❌")

        print("\n📈 SUMMARY:")
        print(f"   Total Checks: {report['total_checks']}")
        print(f"   ✅ Successes: {report['successes']}")
        print(f"   ⚠️  Warnings: {report['warnings']}")
        print(f"   ❌ Critical Issues: {report['critical_issues']}")

        # Display details
        if report["details"]["successes"]:
            print("\n✅ SUCCESSES:")
            for success in report["details"]["successes"]:
                print(f"   {success}")

        if report["details"]["warnings"]:
            print("\n⚠️  WARNINGS:")
            for warning in report["details"]["warnings"]:
                print(f"   {warning}")

        if report["details"]["critical_issues"]:
            print("\n❌ CRITICAL ISSUES:")
            for issue in report["details"]["critical_issues"]:
                print(f"   {issue}")

        if report["recommendations"]:
            print("\n💡 RECOMMENDATIONS:")
            for rec in report["recommendations"]:
                print(f"   {rec}")

        print("\n" + "=" * 60)

        return report["production_ready"]


def main():
    """Main function to run production readiness validation."""
    validator = ProductionReadinessValidator()
    is_ready = validator.run_validation()

    # Exit with appropriate code
    sys.exit(0 if is_ready else 1)


if __name__ == "__main__":
    main()
