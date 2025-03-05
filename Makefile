PO/messages.pot:
	scripts/extract_loclestrings.sh

pot:
	scripts/extract_localestrings.sh

update-po: PO/messages.pot
	scripts/update_po.sh

translations:
	scripts/make_translations.sh
