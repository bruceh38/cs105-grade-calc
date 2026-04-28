#!/usr/bin/env python3

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path


GRADE_VALUES = {
    "excellent": Decimal("100"),
    "very good": Decimal("95"),
    "good": Decimal("85"),
    "fair": Decimal("75"),
    "poor": Decimal("65"),
    "no credit": Decimal("0"),
}

GRADE_ALIASES = {
    "e": "excellent",
    "excellent": "excellent",
    "v": "very good",
    "vg": "very good",
    "very good": "very good",
    "very_good": "very good",
    "g": "good",
    "good": "good",
    "f": "fair",
    "fair": "fair",
    "p": "poor",
    "poor": "poor",
    "n": "no credit",
    "nc": "no credit",
    "no credit": "no credit",
    "no_credit": "no credit",
    "0": "no credit",
}

CONFIG_PATH = Path(__file__).with_name("homework_weights.json")
GRADE_SHORTCUTS = ["e", "v", "g", "f", "p", "n"]
GRADE_LABELS = {
    "e": "Excellent",
    "v": "Very Good",
    "g": "Good",
    "f": "Fair",
    "p": "Poor",
    "n": "No Credit",
}
MAX_HOMEWORK_SCORE = Decimal("100")


def load_config(config_path: Path) -> list[dict]:
    try:
        raw_data = json.loads(config_path.read_text())
    except FileNotFoundError as exc:
        raise SystemExit(
            f"Missing config file: {config_path}\n"
            "Add your homework component weights to homework_weights.json and run again."
        ) from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {config_path}: {exc}") from exc

    if not isinstance(raw_data, list) or len(raw_data) != 9:
        raise SystemExit("Config must be a JSON array with exactly 9 homework entries.")

    validated_homeworks = []
    for homework in raw_data:
        name = homework.get("name")
        components = homework.get("components")
        if not isinstance(name, str) or not name.strip():
            raise SystemExit("Each homework must include a non-empty 'name'.")
        if not isinstance(components, list) or not components:
            raise SystemExit(f"{name} must include a non-empty 'components' list.")

        component_total = Decimal("0")
        validated_components = []

        for component in components:
            label = component.get("name")
            weight = component.get("weight")

            if not isinstance(label, str) or not label.strip():
                raise SystemExit(f"{name} contains a component with an invalid 'name'.")

            try:
                weight_decimal = Decimal(str(weight))
            except (InvalidOperation, TypeError) as exc:
                raise SystemExit(
                    f"{name} -> {label} has an invalid numeric weight: {weight}"
                ) from exc

            if weight_decimal < 0:
                raise SystemExit(f"{name} -> {label} has a negative weight.")

            component_total += weight_decimal
            validated_components.append({"name": label.strip(), "weight": weight_decimal})

        if component_total != Decimal("100"):
            raise SystemExit(f"{name} weights sum to {component_total}, expected 100.")

        validated_homeworks.append({"name": name.strip(), "components": validated_components})

    return validated_homeworks


def score_for_selection(selection: dict, homework: dict) -> Decimal:
    if selection["mode"] == "direct":
        return selection["score"]

    weighted_total = Decimal("0")
    for shortcut, component in zip(selection["grades"], homework["components"]):
        normalized = GRADE_ALIASES[shortcut]
        weighted_total += GRADE_VALUES[normalized] * (component["weight"] / Decimal("100"))
    return weighted_total


def render_homework_table(homeworks: list[dict], selections: list[dict | None]) -> None:
    print()
    print("CS105 Homework Grade Calculator")
    print("Select a homework number to calculate or revise.")
    print("Grades: e=Excellent, v=Very Good, g=Good, f=Fair, p=Poor, n=No Credit")
    print()
    print(f"{'No.':<4} {'Homework':<18} {'Status':<12} {'Grade':>8}")
    print("-" * 48)
    for index, (homework, selection) in enumerate(zip(homeworks, selections), start=1):
        status = "Completed" if selection is not None else "Pending"
        grade = f"{score_for_selection(selection, homework):.2f}%" if selection is not None else "--"
        print(f"{index:<4} {homework['name']:<18} {status:<12} {grade:>8}")
    if all(selection is not None for selection in selections):
        average = sum(
            score_for_selection(selection, homework)
            for homework, selection in zip(homeworks, selections)
            if selection is not None
        ) / Decimal("9")
        print("-" * 48)
        print(f"{'':<35} Average {average:>8.2f}%")
    print()


def prompt_for_menu_choice(homeworks: list[dict], selections: list[dict | None]) -> int:
    while True:
        render_homework_table(homeworks, selections)
        raw_value = input("Choose homework 1-9: ").strip()
        if raw_value in {str(number) for number in range(1, 10)}:
            return int(raw_value) - 1
        print("Invalid choice. Enter a homework number from 1 to 9.")


def prompt_for_direct_score(homework: dict, existing_selection: dict | None) -> dict:
    current_value = ""
    if existing_selection is not None and existing_selection["mode"] == "direct":
        current_value = f" current={existing_selection['score']:.2f}%"

    while True:
        raw_value = input(
            f"{homework['name']} direct score{current_value}\n"
            "Enter total homework grade as a percentage from 0 to 100, or 'b' to go back: "
        ).strip().lower()
        if raw_value == "b":
            return {"mode": "cancel"}

        try:
            score = Decimal(raw_value)
        except InvalidOperation:
            print("Invalid percentage. Enter a number from 0 to 100, or b.")
            continue

        if Decimal("0") <= score <= MAX_HOMEWORK_SCORE:
            return {"mode": "direct", "score": score}

        print("Invalid percentage. Enter a number from 0 to 100, or b.")


def prompt_for_component_selection(homework: dict, existing_selection: dict | None) -> dict:
    existing_grades = []
    if existing_selection is not None and existing_selection["mode"] == "components":
        existing_grades = existing_selection["grades"]

    selections = list(existing_grades)
    component_index = 0
    total_components = len(homework["components"])

    while component_index < total_components:
        component = homework["components"][component_index]
        progress = f"[{component_index + 1}/{total_components}]"
        current_value = ""
        if component_index < len(selections):
            current_value = f" current={GRADE_LABELS[selections[component_index]]}"
        prompt = (
            f"{progress} {homework['name']} - {component['name']} ({component['weight']}%)"
            f"{current_value}\n"
            "Enter grade [e/v/g/f/n, or p], or 'b' to go back: "
        )

        raw_value = input(prompt).strip().lower()
        if raw_value == "b":
            if component_index == 0:
                print("Already at the first component.")
                continue
            component_index -= 1
            continue

        if raw_value not in GRADE_SHORTCUTS:
            print("Invalid entry. Use e, v, g, f, p, n, or b.")
            continue

        if component_index < len(selections):
            selections[component_index] = raw_value
        else:
            selections.append(raw_value)
        component_index += 1

    return {"mode": "components", "grades": selections}


def prompt_for_homework_selection(homework: dict, existing_selection: dict | None) -> dict | None:
    while True:
        print()
        print(f"{homework['name']}")
        print("Type 'c' to enter grades component by component.")
        print("Type 't' to enter the total homework grade directly.")
        print("Type 'b' to return to the homework table.")
        raw_value = input("Choose entry mode [c/t/b]: ").strip().lower()

        if raw_value == "b":
            return existing_selection
        if raw_value == "c":
            return prompt_for_component_selection(homework, existing_selection)
        if raw_value == "t":
            result = prompt_for_direct_score(homework, existing_selection)
            if result["mode"] == "cancel":
                continue
            return result

        print("Invalid choice. Use c, t, or b.")


def print_homework_result(homework: dict, selection: dict) -> None:
    print()
    print(f"{homework['name']} completed")
    if selection["mode"] == "direct":
        print(f"- Direct homework grade entered: {selection['score']:.2f}%")
    else:
        for component, shortcut in zip(homework["components"], selection["grades"]):
            print(f"- {component['name']} ({component['weight']}%): {GRADE_LABELS[shortcut]}")
    print(f"Homework grade: {score_for_selection(selection, homework):.2f}%")
    print()


def main() -> None:
    homeworks = load_config(CONFIG_PATH)
    selections: list[dict | None] = [None] * 9

    while not all(selection is not None for selection in selections):
        homework_index = prompt_for_menu_choice(homeworks, selections)
        selection = prompt_for_homework_selection(
            homeworks[homework_index],
            selections[homework_index],
        )
        if selection is None:
            continue
        selections[homework_index] = selection
        print_homework_result(homeworks[homework_index], selection)

    render_homework_table(homeworks, selections)
    print("All homework grades have been entered.")


if __name__ == "__main__":
    main()
