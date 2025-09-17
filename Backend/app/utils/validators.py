from flask import request, jsonify
from functools import wraps

# ** Functions for input validation, such as checking JSON payloads or query parameters.


def validate_input(schema):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            errors = {}
            for key, val_type in schema.items():
                if key not in request.json:
                    errors[key] = "Missing field"
                elif not isinstance(request.json[key], val_type):
                    errors[key] = f"Must be of type {val_type.__name__}"
            if errors:
                return jsonify({"errors": errors}), 400
            return fn(*args, **kwargs)

        return wrapper

    return decorator


# Example schema
schema = {"username": str, "age": int}
