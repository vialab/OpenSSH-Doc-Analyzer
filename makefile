.PHONY: tran-extract tran-update tran-compile pretranslation translations

tran-extract :
	pybabel extract -F babel.cfg -k _l -o translations/messages.pot \
	--msgid-bugs-address="vialab.research@gmail.com" \
	--copyright-holder="Vialab" \
	--project="Synonymic Search" \
	--version="1.0" .

tran-update :
	pybabel update -i translations/messages.pot -d translations

tran-compile :
	pybabel compile -d translations

pretranslation : tran-extract tran-update
translations : tran-compile