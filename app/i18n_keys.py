"""Liste de tous les textes à traduire (utilisée par les tests pour vérifier les traductions)."""
import ast
import os

from jinja2 import Environment, nodes

APP_DIR = os.path.dirname(__file__)


def _python_keys(path):
    tree = ast.parse(open(path, encoding="utf-8").read())
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_"
                and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
            yield node.args[0].value


def _template_keys(env, path):
    tree = env.parse(open(path, encoding="utf-8").read())
    for call in tree.find_all(nodes.Call):
        if isinstance(call.node, nodes.Name) and call.node.name == "_" and call.args \
                and isinstance(call.args[0], nodes.Const) and isinstance(call.args[0].value, str):
            yield call.args[0].value


def dynamic_keys():
    """Valeurs traduites via _(variable) : statuts, listes de choix, variables de modèles…"""
    from .i18n import JS_TEXTS
    from .models import CONTRACT_STATUSES, VEHICLE_STATUSES, FUEL_TYPES, FUEL_LEVELS, PAYMENT_METHODS
    from .utils import PLACEHOLDERS

    keys = set(JS_TEXTS)
    keys |= set(CONTRACT_STATUSES.values()) | set(VEHICLE_STATUSES.values())
    keys |= set(FUEL_TYPES) | set(FUEL_LEVELS) | set(PAYMENT_METHODS)
    keys |= {"Manuelle", "Automatique", "CIN", "passeport"}
    keys |= set(PLACEHOLDERS.values())
    return keys


def all_keys():
    env = Environment()
    keys = set()
    for folder, _dirs, files in os.walk(APP_DIR):
        for name in files:
            path = os.path.join(folder, name)
            if name.endswith(".py"):
                keys |= set(_python_keys(path))
            elif name.endswith(".html"):
                keys |= set(_template_keys(env, path))
    return keys | dynamic_keys()
