from flask import Blueprint, jsonify, request

from ..services.journal import get_journal_positions, update_journal
from ..storage import database


journal_api = Blueprint("journal", __name__, url_prefix="/api")


@journal_api.get("/journal")
def journal():
    return jsonify(get_journal_positions(request.args))


@journal_api.put("/journal/<path:position_id>")
def save_journal(position_id):
    try:
        return jsonify(update_journal(position_id, request.get_json(silent=True)))
    except ValueError as error:
        return jsonify(error=str(error)), 400
    except LookupError as error:
        return jsonify(error=str(error)), 404


@journal_api.put("/positions/<path:position_id>/notes")
def position_notes(position_id):
    notes = request.get_json()
    database.save_position_notes(
        position_id,
        notes.get("entry_note", ""),
        notes.get("exit_note", ""),
    )
    return jsonify(entry_note=notes.get("entry_note", ""), exit_note=notes.get("exit_note", ""))
