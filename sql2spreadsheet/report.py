from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort

from sql2spreadsheet.auth import login_required
from sql2spreadsheet.db import get_db

bp = Blueprint("report", __name__)


@bp.route("/")
def index():
    db = get_db()
    reports = db.execute(
        "SELECT p.id, title, sqlcommand, created_at, requester_id, email"
        " FROM report p JOIN user u ON p.requester_id = u.id "
        " ORDER BY created_at DESC"
    ).fetchall()
    return render_template("report/index.html", reports=reports)


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        title = request.form["title"]
        sqlcommand = request.form["sqlcommand"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "INSERT INTO report (title, sqlcommand, requester_id, registrant_id)"
                " VALUES (?, ?, ?, ?)",
                (title, sqlcommand, g.user["id"], g.user["id"]),
            )
            db.commit()
            return redirect(url_for("report.index"))

    return render_template("report/create.html")


def get_report(id, check_requester=True):
    report = (
        get_db()
        .execute(
            "SELECT p.id, title, sqlcommand, created_at, requester_id, email, registrant_id"
            " FROM report p JOIN user u ON p.requester_id = u.id"
            " WHERE p.id = ?",
            (id,),
        )
        .fetchone()
    )

    if report is None:
        abort(404, f"Report id {id} doesn't exist.")

    if check_requester and report["requester_id"] != g.user["id"]:
        abort(403)

    return report


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    report = get_report(id)

    if request.method == "POST":
        title = request.form["title"]
        sqlcommand = request.form["sqlcommand"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "UPDATE report SET title = ?, sqlcommand = ?" " WHERE id = ?",
                (title, sqlcommand, id),
            )
            db.commit()
            return redirect(url_for("report.index"))

    return render_template("report/update.html", report=report)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    get_report(id)
    db = get_db()
    db.execute("DELETE FROM report WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("report.index"))
