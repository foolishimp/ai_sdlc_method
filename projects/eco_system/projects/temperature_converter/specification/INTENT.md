# Intent: Temperature Converter Library

## Problem Statement

We need a Python library that converts between Celsius, Fahrenheit,
and Kelvin temperature scales. The library must be correct, well-tested,
and provide clear error messages for invalid inputs.

## Requirements

### REQ-F-CONV-001: Temperature Conversion Functions

Provide 6 conversion functions:
- `celsius_to_fahrenheit(c)` — Formula: F = C * 9/5 + 32
- `fahrenheit_to_celsius(f)` — Formula: C = (F - 32) * 5/9
- `celsius_to_kelvin(c)` — Formula: K = C + 273.15
- `kelvin_to_celsius(k)` — Formula: C = K - 273.15
- `fahrenheit_to_kelvin(f)` — via Celsius intermediate
- `kelvin_to_fahrenheit(k)` — via Celsius intermediate

Acceptance criteria:
- celsius_to_fahrenheit(0) == 32.0
- celsius_to_fahrenheit(100) == 212.0
- fahrenheit_to_celsius(32) == 0.0
- fahrenheit_to_celsius(212) == 100.0
- celsius_to_kelvin(0) == 273.15
- kelvin_to_celsius(273.15) == 0.0
- fahrenheit_to_kelvin(32) == 273.15
- kelvin_to_fahrenheit(273.15) == 32.0

### REQ-F-CONV-002: Input Validation

All conversion functions must validate inputs:
- Non-numeric input raises TypeError with descriptive message
- Below absolute zero raises ValueError:
  - Celsius below -273.15
  - Fahrenheit below -459.67
  - Kelvin below 0

## Scope

- Pure Python, no external dependencies
- Single module: `src/temperature_converter.py`
- 100% test coverage for conversion logic
