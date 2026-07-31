/** @odoo-module **/

import { Component, onWillStart, onWillUpdateProps, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { formatDateTime, deserializeDateTime } from "@web/core/l10n/dates";

export class StickyNotesPanel extends Component {
    static template = "quick_sticky_notes.StickyNotesPanel";
    static props = {
        resModel: String,
        resId: { type: Number, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({
            enabled: false,
            loading: true,
            collapsed: false,
            notes: [],
            colors: [],
            editingId: null,
            draft: this._emptyDraft(),
            showForm: false,
        });

        onWillStart(() => this.loadNotes(this.props.resModel, this.props.resId));
        onWillUpdateProps((nextProps) => {
            if (
                nextProps.resModel !== this.props.resModel ||
                nextProps.resId !== this.props.resId
            ) {
                return this.loadNotes(nextProps.resModel, nextProps.resId);
            }
        });
    }

    _emptyDraft() {
        return {
            name: "",
            body: "",
            color: "yellow",
            is_pinned: false,
            visibility: "private",
        };
    }

    get canShow() {
        return Boolean(this.props.resId) && this.state.enabled;
    }

    get noteCount() {
        return this.state.notes.length;
    }

    async loadNotes(resModel, resId) {
        this.state.loading = true;
        this.state.showForm = false;
        this.state.editingId = null;
        this.state.draft = this._emptyDraft();
        if (!resId) {
            this.state.enabled = false;
            this.state.notes = [];
            this.state.loading = false;
            return;
        }
        try {
            const data = await this.orm.call("quick.sticky.note", "get_panel_data", [
                resModel,
                resId,
            ]);
            this.state.enabled = Boolean(data.enabled);
            this.state.notes = data.notes || [];
            this.state.colors = data.colors || [];
        } catch (error) {
            this.state.enabled = false;
            this.state.notes = [];
            console.error("Quick Sticky Notes: failed to load panel", error);
        } finally {
            this.state.loading = false;
        }
    }

    toggleCollapsed() {
        this.state.collapsed = !this.state.collapsed;
    }

    openCreate() {
        this.state.editingId = null;
        this.state.draft = this._emptyDraft();
        this.state.showForm = true;
        this.state.collapsed = false;
    }

    openEdit(note) {
        if (!note.is_author) {
            this.notification.add(_t("Only the author can edit this note."), {
                type: "warning",
            });
            return;
        }
        this.state.editingId = note.id;
        this.state.draft = {
            name: note.name || "",
            body: note.body || "",
            color: note.color || "yellow",
            is_pinned: Boolean(note.is_pinned),
            visibility: note.visibility || "private",
        };
        this.state.showForm = true;
        this.state.collapsed = false;
    }

    cancelForm() {
        this.state.showForm = false;
        this.state.editingId = null;
        this.state.draft = this._emptyDraft();
    }

    async saveNote() {
        const body = (this.state.draft.body || "").trim();
        if (!body) {
            this.notification.add(_t("Please write a note before saving."), {
                type: "warning",
            });
            return;
        }
        try {
            if (this.state.editingId) {
                const updated = await this.orm.call(
                    "quick.sticky.note",
                    "update_from_panel",
                    [[this.state.editingId], {
                        name: this.state.draft.name,
                        body,
                        color: this.state.draft.color,
                        is_pinned: this.state.draft.is_pinned,
                        visibility: this.state.draft.visibility,
                    }]
                );
                this.state.notes = this.state.notes.map((n) =>
                    n.id === updated.id ? updated : n
                );
                this._sortNotes();
            } else {
                const created = await this.orm.call(
                    "quick.sticky.note",
                    "create_from_panel",
                    [{
                        name: this.state.draft.name,
                        body,
                        color: this.state.draft.color,
                        is_pinned: this.state.draft.is_pinned,
                        visibility: this.state.draft.visibility,
                        res_model: this.props.resModel,
                        res_id: this.props.resId,
                    }]
                );
                this.state.notes = [...this.state.notes, created];
                this._sortNotes();
            }
            this.cancelForm();
            this.notification.add(_t("Sticky note saved."), { type: "success" });
        } catch (error) {
            this.notification.add(
                error?.data?.message || _t("Could not save the sticky note."),
                { type: "danger" }
            );
        }
    }

    async togglePin(note) {
        if (!note.is_author) {
            return;
        }
        try {
            const updated = await this.orm.call(
                "quick.sticky.note",
                "update_from_panel",
                [[note.id], { is_pinned: !note.is_pinned }]
            );
            this.state.notes = this.state.notes.map((n) =>
                n.id === updated.id ? updated : n
            );
            this._sortNotes();
        } catch (error) {
            this.notification.add(
                error?.data?.message || _t("Could not update the sticky note."),
                { type: "danger" }
            );
        }
    }

    async deleteNote(note) {
        if (!note.is_author) {
            this.notification.add(_t("Only the author can delete this note."), {
                type: "warning",
            });
            return;
        }
        try {
            await this.orm.call("quick.sticky.note", "delete_from_panel", [[note.id]]);
            this.state.notes = this.state.notes.filter((n) => n.id !== note.id);
            if (this.state.editingId === note.id) {
                this.cancelForm();
            }
            this.notification.add(_t("Sticky note deleted."), { type: "success" });
        } catch (error) {
            this.notification.add(
                error?.data?.message || _t("Could not delete the sticky note."),
                { type: "danger" }
            );
        }
    }

    _sortNotes() {
        this.state.notes = [...this.state.notes].sort((a, b) => {
            if (a.is_pinned !== b.is_pinned) {
                return a.is_pinned ? -1 : 1;
            }
            return String(b.write_date || "").localeCompare(String(a.write_date || ""));
        });
    }

    colorLabel(color) {
        const found = this.state.colors.find((c) => c[0] === color);
        return found ? found[1] : color;
    }

    formatDate(value) {
        if (!value) {
            return "";
        }
        try {
            return formatDateTime(deserializeDateTime(value));
        } catch {
            return value;
        }
    }
}
