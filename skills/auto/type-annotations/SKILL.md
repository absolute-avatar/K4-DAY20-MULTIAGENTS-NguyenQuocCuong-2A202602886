---
name: type-annotations
description: Use when ensuring all public functions have type annotations.
---
1. Review all public functions in the codebase (those not starting with '_').
2. For each function, check that all parameters have type annotations.
3. Verify that the return value of each function has a type annotation.
4. If any function is missing type annotations, add them according to the expected types.
5. After making changes, run the test suite to ensure no errors are introduced.
6. Consult the task specification for any specific type requirements or examples.
