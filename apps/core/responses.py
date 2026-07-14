from rest_framework.response import Response


def success_response(
    data=None,
    message="Success",
    status_code=200,
):
    """
    Standard success response.
    """

    return Response(
        {
            "success": True,
            "status_code": status_code,
            "message": message,
            "data": data,
        },
        status=status_code,
    )