# CS105 Grade Calculator

This is a local command line tool for calculating the cumulative homework grade for CS105.

## Grading scale

- `e` = excellent = 100
- `v` = very good = 95
- `g` = good = 85
- `f` = fair = 75
- `p` = poor = 65
- `n` = no credit = 0

## How it works

1. The calculator reads the component weights for all 9 homeworks from `homework_weights.json`.
2. It shows a table of all 9 homeworks with completion status and computed grades.
3. You choose any homework by typing `1` through `9`.
4. For each homework, you can either enter grades component by component or enter the total homework percentage directly.
5. In component mode, it prompts for each component using short grade codes.
6. You can type `b` during component entry to go back one component and change a previous selection.
7. After a homework is completed, the tool returns to the table and shows that homework's grade.
8. When all 9 homeworks are completed, it shows the overall average.

## Run it

```bash
python3 cs105_grade_calc.py
```

## Next step

Replace the placeholder entries in `homework_weights.json` with the real component names and weights for each of the 9 homeworks.
