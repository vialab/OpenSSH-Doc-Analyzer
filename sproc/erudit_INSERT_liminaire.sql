DELIMITER //
SET NAMES utf8mb4;//
SET CHARACTER SET utf8mb4; //
SET character_set_connection=utf8mb4;//
SET collation_connection = 'utf8mb4_unicode_ci';//
drop procedure if exists erudit_INSERT_liminaire;
//

CREATE PROCEDURE `erudit_INSERT_liminaire`(
    documentid int
    , erudit_xml longtext
)
begin
    
    declare v_row_index int unsigned;
    declare v_row_count int unsigned;
    
    declare v_child_index int unsigned;
    declare v_child_count int unsigned;
    
    declare v_ref_index int unsigned;
    declare v_ref_count int unsigned;
    
    declare v_xpath_row varchar(255);
    declare v_xpath_child varchar(255);
    declare v_xpath_ref varchar(255);
    
    declare v_title varchar(200);
    declare v_subtitle varchar(200);
    declare v_lang varchar(200);
    
    -- save off the raw xml
	insert into raw_liminaire(documentid, rawxml) values(documentid, erudit_xml);
    
	-- Save general notes
	set v_row_count := extractValue(erudit_xml,'count(/liminaire/notegen)');
	set v_row_index := 0;
    
	-- loop through all the row elements
    while v_row_index < v_row_count do
		set v_row_index := v_row_index + 1;
        set v_xpath_row := concat('/liminaire/notegen[', v_row_index, ']');
	
        insert into note(
			documentid
            , notetype
            , titre
            , note
            , prenom
            , autreprenom
            , nomfamille
            , suffixe
        ) values (
			documentid
            , 'liminaire_general'
            , extractValue(erudit_xml, concat(v_xpath_row,'/titre[1]//text()'))
            , extractValue(erudit_xml, concat(v_xpath_row,'/alinea[1]//text()'))
            , extractValue(erudit_xml, concat(v_xpath_row,'/auteur/nompers/prenom[1]//text()'))
            , extractValue(erudit_xml, concat(v_xpath_row,'/auteur/nompers/autreprenom[1]//text()'))
            , extractValue(erudit_xml, concat(v_xpath_row,'/auteur/nompers/nomfamille[1]//text()'))
            , extractValue(erudit_xml, concat(v_xpath_row,'/auteur/nompers/suffixe[1]//text()'))
        );
	end while;
    
	-- Save title information
	set v_row_count := extractValue(erudit_xml,'count(/liminaire/grtitre)');
	set v_row_index := 0;
    
	-- loop through all the row elements
    while v_row_index < v_row_count do
		set v_row_index := v_row_index + 1;
        set v_xpath_row := concat('/liminaire/grtitre[', v_row_index, ']');
		
        insert into titre(
			documentid
            , surtitre
            , titre
            , sstitre
            , trefbiblio
        ) values (
			documentid
            , extractValue(erudit_xml, concat(v_xpath_row,'/surtitre//text()'))
            , extractValue(erudit_xml, concat(v_xpath_row,'/titre//text()'))
            , extractValue(erudit_xml, concat(v_xpath_row,'/sstitre//text()'))
            , extractValue(erudit_xml, concat(v_xpath_row,'/trefbiblio//text()'))
        );
	end while;
    
    -- Save resume
	set v_row_count := extractValue(erudit_xml,'count(/liminaire/resume)');
	set v_row_index := 0;
    
	-- loop through all the row elements
    while v_row_index < v_row_count do
		set v_row_index := v_row_index + 1;
        set v_xpath_row := concat('/liminaire/resume[', v_row_index, ']');
		
        insert into summary(
			documentid
            , titre
            , lang
            , txt
        ) values (
			documentid
            , extractValue(erudit_xml, concat(v_xpath_row,'/titre[1]//text()'))
            , extractValue(erudit_xml, concat(v_xpath_row,'/@lang'))
            , extractValue(erudit_xml, concat(v_xpath_row,'/alinea[1]//text()'))
        );
	end while;
    
    -- Save authors
	set v_row_count := extractValue(erudit_xml,'count(/liminaire/grauteur/auteur)');
	set v_row_index := 0;
    
	-- loop through all the row elements
    while v_row_index < v_row_count do
		set v_row_index := v_row_index + 1;
        set v_xpath_row := concat('/liminaire/grauteur/auteur[', v_row_index, ']');
		
        insert into auteur(
			documentid
            , auteurpos
            , prenom
            , autreprenom
            , nomfamille
			, suffixe
            , nomorg
        ) values (
			documentid
            , extractValue(erudit_xml, concat(v_xpath_row,'/@id'))
            , extractValue(erudit_xml, concat(v_xpath_row,'/nompers/prenom//text()'))
            , extractValue(erudit_xml, concat(v_xpath_row,'/nompers/autreprenom//text()'))
            , extractValue(erudit_xml, concat(v_xpath_row,'/nompers/nomfamille//text()'))
            , extractValue(erudit_xml, concat(v_xpath_row,'/nompers/suffixe//text()'))
            , extractValue(erudit_xml, concat(v_xpath_row,'/nompers/nomorg//text()'))
        );
	end while;
    
    
    -- Save grouped key words
	set v_row_count := extractValue(erudit_xml,'count(/liminaire/grmotcle)');
	set v_row_index := 0;
    
	-- loop through all the row elements
    while v_row_index < v_row_count do
		set v_row_index := v_row_index + 1;
        set v_xpath_row := concat('/liminaire/grmotcle[', v_row_index, ']');
		set v_title := extractValue(erudit_xml, concat(v_xpath_row,'/titre[1]//text()'));
        set v_lang := extractValue(erudit_xml, concat(v_xpath_row,'/@lang'));
        
        set v_child_count := extractValue(erudit_xml, concat('count(', v_xpath_row, '/motcle)'));
		set v_child_index := 0;
		
		while v_child_index < v_child_count do        
			set v_child_index := v_child_index + 1;
			set v_xpath_child := concat(v_xpath_row, '/motcle[', v_child_index, ']');
            
			insert into motcle(
				documentid
                , titre
				, lang
				, motcle
			) values (
				documentid
				, v_title
				, v_lang
				, extractValue(erudit_xml, concat(v_xpath_row,'//text()'))
			);
		end while;
        
	end while;
    
    commit;
end