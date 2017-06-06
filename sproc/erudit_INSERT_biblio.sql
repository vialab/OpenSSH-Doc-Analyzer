DELIMITER //

SET NAMES utf8mb4;//
SET CHARACTER SET utf8mb4; //
SET character_set_connection=utf8mb4;//
SET collation_connection = 'utf8mb4_unicode_ci';//

drop procedure if exists erudit_INSERT_biblio;
//

CREATE PROCEDURE `erudit_INSERT_biblio`(
    documentid int
    , erudit_xml longtext
)
begin
    
    declare v_parent_index int unsigned;
    declare v_parent_count int unsigned;
    
    declare v_row_index int unsigned;
    declare v_row_count int unsigned;
    
    declare v_child_index int unsigned;
    declare v_child_count int unsigned;
    
    declare v_ref_index int unsigned;
    declare v_ref_count int unsigned;
    
    declare v_xpath_parent varchar(255);
    declare v_xpath_row varchar(255);
    declare v_xpath_child varchar(255);
    declare v_xpath_ref varchar(255);
    
    declare v_title varchar(200);
    declare v_subtitle varchar(200);
    declare v_lang varchar(200);
    
    -- save off the raw xml
	insert into raw_biblio(documentid, rawxml) values(documentid, erudit_xml);
    
    
    set v_parent_count := extractValue(erudit_xml,'count(/partiesann)');
	set v_parent_index := 0;
    
    while v_parent_index < v_parent_count do
		set v_parent_index := v_parent_index + 1;
        set v_xpath_parent := concat('/partiesann[', v_parent_index, ']');
    
		-- First save all references from a flat biblio (i.e. /biblio[n]/refbiblio)
		set v_row_count := extractValue(erudit_xml, concat('count(', v_xpath_parent, '/grbiblio/biblio)'));
		set v_row_index := 0;
		set v_lang := extractValue(erudit_xml, concat(v_xpath_parent, '/@lang'));
		-- loop through all the row elements
		while v_row_index < v_row_count do
			set v_row_index := v_row_index + 1;
			set v_xpath_row := concat(v_xpath_parent,'/grbiblio/biblio[', v_row_index, ']');
			-- get the title of this reference list
			set v_title := extractValue(erudit_xml, concat(v_xpath_row,'/titre/text()'));
			
			-- Save all flat references first
			set v_child_count := extractValue(erudit_xml, concat('count(', v_xpath_row, '/refbiblio)'));
			set v_child_index := 0;
		
			while v_child_index < v_child_count do        
				set v_child_index := v_child_index + 1;
				set v_xpath_child := concat(v_xpath_row, '/refbiblio[', v_child_index, ']');
				
				insert into biblio (
					documentid
					, title
					, reference
					, url
					, refpos
					, lang
				) values (
					documentid
					, v_title
					, extractValue(erudit_xml, concat(v_xpath_child,'//text()'))
					, extractValue(erudit_xml, concat(v_xpath_child,'/liensimple[1]//text()'))
					, extractValue(erudit_xml, concat(v_xpath_child,'/@id'))
					, v_lang
				);
				
			end while;
		
			-- Now save all nested (non-flat) references (i.e. /biblio[n]/divbiblio[m]/refbiblio)
			-- This sometimes happens when there are multiple lists (e.g. bibliographie, discographie, etc.)
			set v_child_count := extractValue(erudit_xml, concat('count(', v_xpath_row, '/divbiblio)'));
			set v_child_index := 0;
			
			while v_child_index < v_child_count do        
				set v_child_index := v_child_index + 1;
				set v_xpath_child := concat(v_xpath_row, '/divbiblio[', v_child_index, ']');
				
				-- get the sub titles of this reference list
				set v_title := extractValue(erudit_xml, concat(v_xpath_row,'/titre//text()'));
				
				-- get the references for this nested element
				set v_ref_count := extractValue(erudit_xml, concat('count(', v_xpath_ref, '/refbiblio)'));
				set v_ref_index := 0;
				
				while v_ref_index < v_ref_count do
					set v_ref_index := v_ref_index + 1;
					set v_xpath_ref := concat(v_xpath_child, '/refbiblio[', v_ref_index, ']');
				
					insert into biblio (
						documentid
						, title
						, subtitle
						, reference
						, url
						, refpos
						, lang
					) values (
						documentid
						, v_title
						, v_subtitle
						, extractValue(erudit_xml, concat(v_xpath_ref,'//text()'))
						, extractValue(erudit_xml, concat(v_xpath_ref,'/liensimple[1]//text()'))
						, extractValue(erudit_xml, concat(v_xpath_ref,'/@id'))
						, v_lang
					);
				end while;
				
			end while;
		end while;
		
		 -- Save all our notes
		set v_row_count := extractValue(erudit_xml, concat('count(', v_xpath_parent, '/grnote/note)'));
		set v_row_index := 0;
		
		-- loop through all the row elements
		while v_row_index < v_row_count do
			set v_row_index := v_row_index + 1;
			set v_xpath_row := concat(v_xpath_parent, '/grnote/note[', v_row_index, ']');
			
			insert into note (
				documentid
				, notetype
				, notepos
				, note
			) values (
				documentid
				, 'biblio_general'
				, extractValue(erudit_xml, concat(v_xpath_child,'/no/text()'))
				, extractValue(erudit_xml, concat(v_xpath_child,'/alinea//text()'))
			);
		end while;
		
		-- Save biographic notes
		set v_row_count := extractValue(erudit_xml,concat('count(', v_xpath_parent, '/grnotebio/notebio)'));
		set v_row_index := 0;
		
		-- loop through all the row elements
		while v_row_index < v_row_count do
			set v_row_index := v_row_index + 1;
			set v_xpath_row := concat(v_xpath_parent, '/grnotebio/notebio[', v_row_index, ']');
			
			insert into note(
				documentid
				, notetype
				, note
				, prenom
				, autreprenom
				, nomfamille
				, suffixe
			) values (
				documentid
				, 'biblio_bio'
				, extractValue(erudit_xml, concat(v_xpath_row,'/alinea[1]//text()'))
				, extractValue(erudit_xml, concat(v_xpath_row,'/nompers/prenom[1]//text()'))
				, extractValue(erudit_xml, concat(v_xpath_row,'/nompers/autreprenom[1]//text()'))
				, extractValue(erudit_xml, concat(v_xpath_row,'/nompers/nomfamille[1]//text()'))
				, extractValue(erudit_xml, concat(v_xpath_row,'/nompers/suffixe[1]//text()'))
			);
		end while;
		
    end while;
    commit;
end