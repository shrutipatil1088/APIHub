from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return response

    message = "Something went wrong."
    errors = None

    if isinstance(response.data, dict):
        if "detail" in response.data:
            message = str(response.data["detail"])
        else:
            message = "Validation failed."
            errors = response.data
    else:
        errors = response.data

    response.data = {
        "success": False,
        "status_code": response.status_code,
        "message": message,
        "data": None,
        "errors": errors,
    }

    return response