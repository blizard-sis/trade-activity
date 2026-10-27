import sqlite3

from flask import Blueprint, jsonify, request, send_file

from ..services import plans as service

plans_api = Blueprint("plans", __name__, url_prefix="/api/plans")
attachments_api = Blueprint("attachments", __name__, url_prefix="/api/attachments")


@plans_api.errorhandler(ValueError)
@attachments_api.errorhandler(ValueError)
def invalid(error):
    return jsonify(error=str(error)), 400


@plans_api.errorhandler(LookupError)
@attachments_api.errorhandler(LookupError)
def missing(error):
    return jsonify(error=str(error)), 404


@plans_api.errorhandler(sqlite3.IntegrityError)
def conflict(error):
    return jsonify(error="Эта запись уже существует"), 409


@plans_api.get("")
def plans():
    return jsonify(service.list_plans(request.args))


@plans_api.get("/available-positions")
def available_positions():
    return jsonify(service.available_positions(request.args))


@plans_api.post("")
def create_plan():
    return jsonify(service.create_plan(request.get_json(silent=True))), 201


@plans_api.get("/<plan_id>")
def plan(plan_id):
    return jsonify(service.get_plan(plan_id))


@plans_api.put("/<plan_id>")
def update_plan(plan_id):
    return jsonify(service.update_plan(plan_id, request.get_json(silent=True)))


@plans_api.delete("/<plan_id>")
def delete_plan(plan_id):
    return jsonify(service.delete_plan(plan_id))


@plans_api.post("/<plan_id>/positions")
def link_position(plan_id):
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or not isinstance(body.get("position_id"), str):
        raise ValueError("Выберите позицию")
    return jsonify(service.link_position(plan_id, body["position_id"]))


@plans_api.delete("/<plan_id>/positions/<path:position_id>")
def unlink_position(plan_id, position_id):
    return jsonify(service.unlink_position(plan_id, position_id))


@plans_api.post("/<plan_id>/attachments")
def add_attachment(plan_id):
    request.max_content_length = 60 * 1024 * 1024
    upload = request.files.get("file")
    if upload is None:
        raise ValueError("Выберите изображение")
    return (
        jsonify(
            service.add_attachment(
                plan_id,
                upload,
                caption=request.form.get("caption", ""),
            )
        ),
        201,
    )


@attachments_api.get("/<attachment_id>")
def attachment(attachment_id):
    path, mime = service.attachment_file(attachment_id)
    return send_file(path, mimetype=mime, conditional=True)


@attachments_api.delete("/<attachment_id>")
def delete_attachment(attachment_id):
    return jsonify(service.delete_attachment(attachment_id))
