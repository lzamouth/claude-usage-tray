"""Translation catalog checks: every string used in the code is translated."""

from __future__ import annotations

import ast
import importlib
import string
import unittest
from pathlib import Path

from claude_usage_tray import i18n

PACKAGE_DIR = Path(__file__).resolve().parent.parent / "claude_usage_tray"

# Tuples of strings translated indirectly (``_(NAME[i])``), per module.
INDIRECT_TUPLES = {"tray.py": ("WEEKDAYS",)}


def _source_messages() -> set[str]:
	"""Collect every literal passed to ``_()`` plus indirectly translated tuples."""
	messages: set[str] = set()
	for path in PACKAGE_DIR.rglob("*.py"):
		if "locales" in path.parts:
			continue
		tree = ast.parse(path.read_text(encoding="utf-8"))
		wanted_tuples = INDIRECT_TUPLES.get(path.name, ())
		for node in ast.walk(tree):
			if (
				isinstance(node, ast.Call)
				and isinstance(node.func, ast.Name)
				and node.func.id == "_"
				and node.args
				and isinstance(node.args[0], ast.Constant)
				and isinstance(node.args[0].value, str)
			):
				messages.add(node.args[0].value)
			elif (
				isinstance(node, ast.Assign)
				and len(node.targets) == 1
				and isinstance(node.targets[0], ast.Name)
				and node.targets[0].id in wanted_tuples
			):
				messages.update(ast.literal_eval(node.value))
	return messages


def _placeholders(message: str) -> set[str]:
	return {field for _text, field, _spec, _conv in string.Formatter().parse(message) if field}


class CatalogTest(unittest.TestCase):
	def setUp(self) -> None:
		self.messages = _source_messages()

	def test_messages_found(self) -> None:
		self.assertGreater(len(self.messages), 20)

	def test_catalogs_complete_and_consistent(self) -> None:
		for code in i18n.SUPPORTED_LANGUAGES:
			if code == i18n.SOURCE_LANGUAGE:
				continue
			with self.subTest(language=code):
				catalog = importlib.import_module(f"claude_usage_tray.locales.{code}").MESSAGES
				self.assertEqual(set(), self.messages - catalog.keys(), "missing translations")
				self.assertEqual(set(), catalog.keys() - self.messages, "stale translations")
				for source, translated in catalog.items():
					self.assertEqual(
						_placeholders(source), _placeholders(translated), source
					)


class LanguageSelectionTest(unittest.TestCase):
	def tearDown(self) -> None:
		i18n.set_language("en")

	def test_detect_language(self) -> None:
		cases = [
			({"LANG": "fr_BE.UTF-8"}, "fr"),
			({"LANGUAGE": "de_DE:fr_FR:en", "LANG": "de_DE.UTF-8"}, "fr"),
			({"LC_ALL": "C", "LANG": "fr_FR.UTF-8"}, "en"),
			({"LANG": "de_DE.UTF-8"}, "en"),
			({}, "en"),
		]
		for env, expected in cases:
			with self.subTest(env=env):
				self.assertEqual(expected, i18n.detect_language(env))

	def test_set_language(self) -> None:
		self.assertEqual("fr", i18n.set_language("FR"))
		self.assertEqual("Quitter", i18n._("Quit"))
		self.assertEqual("en", i18n.set_language("xx"))
		self.assertEqual("Quit", i18n._("Quit"))


if __name__ == "__main__":
	unittest.main()
