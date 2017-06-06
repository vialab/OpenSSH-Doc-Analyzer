DELIMITER //
SET NAMES utf8mb4;//
SET CHARACTER SET utf8mb4; //
SET character_set_connection=utf8mb4;//
SET collation_connection = 'utf8mb4_unicode_ci';//
drop procedure if exists erudit_INSERT_entity;
//

create procedure erudit_INSERT_entity(
    documentid int
    , erudit_xml longtext
)
begin
    declare v_row_index int unsigned;
    declare v_row_count int unsigned;
    declare v_xpath_row varchar(255);
    

    -- Save all text that was in a marquage
    set v_row_count := extractValue(erudit_xml,'count(/descendant-or-self::marquage)');
	set v_row_index := 0;
    -- loop through all the row elements
    while v_row_index < v_row_count do        
        set v_row_index := v_row_index + 1;
        set v_xpath_row := concat(
            '/descendant-or-self::marquage['
        ,   v_row_index
        ,   ']'
        );
        
        if (extractValue(erudit_xml, concat(v_xpath_row,'//text()')) != '') then
        
			insert into entity(
				documentid
				, entity
				, entitytype
				, txt
			) values (
				documentid
				, 'marquage'
				, extractValue(erudit_xml, concat(v_xpath_row,'/@typemarq'))
				, extractValue(erudit_xml, concat(v_xpath_row,'//text()'))
			);
        
        end if;
    end while;
    
    -- Save all organizations
    set v_row_count := extractValue(erudit_xml,'count(/descendant-or-self::nomorg)');
	set v_row_index := 0;
    -- loop through all the row elements
    while v_row_index < v_row_count do        
        set v_row_index := v_row_index + 1;
        set v_xpath_row := concat(
            '/descendant-or-self::nomorg['
        ,   v_row_index
        ,   ']'
        );

		-- only do this when we actually have a value
        -- if ( extractValue(erudit_xml, concat(v_xpath_row,'//text()')) != '' ) then
        
			insert into entity(
				documentid
				, entity
				, txt
			) values (
				documentid
				, 'nomorg'
				, extractValue(erudit_xml, concat(v_xpath_row, '//text()'))
			);        
        -- end if;
    end while;
    
    -- Save all people
    set v_row_count := extractValue(erudit_xml,'count(/descendant-or-self::nompers)');
	set v_row_index := 0;
    -- loop through all the row elements
    while v_row_index < v_row_count do        
        set v_row_index := v_row_index + 1;
        set v_xpath_row := concat(
            '/descendant-or-self::nompers['
        ,   v_row_index
        ,   ']'
        );
        
        -- only do this when we actually have a value
        if (concat(extractValue(erudit_xml, concat(v_xpath_row,'/prenom//text()'))
				, extractValue(erudit_xml, concat(v_xpath_row,'/autreprenom//text()'))
                , extractValue(erudit_xml, concat(v_xpath_row,'/nomfamille//text()'))
                , extractValue(erudit_xml, concat(v_xpath_row,'/suffixe//text()'))
                , extractValue(erudit_xml, concat(v_xpath_row,'/nomorg//text()'))) != '') then
                
			insert into entity(
				documentid
				, entity
				, txt
			) values (
				documentid
				, 'nompers'
				, concat(extractValue(erudit_xml, concat(v_xpath_row,'/prenom//text()'))
					, extractValue(erudit_xml, concat(v_xpath_row,'/autreprenom//text()'))
					, extractValue(erudit_xml, concat(v_xpath_row,'/nomfamille//text()'))
					, extractValue(erudit_xml, concat(v_xpath_row,'/suffixe//text()'))
					, extractValue(erudit_xml, concat(v_xpath_row,'/nomorg//text()'))
				)
			);
            
		end if;
    end while;
    
    commit;
end;