DELIMITER //
SET NAMES utf8mb4;//
SET CHARACTER SET utf8mb4; //
SET character_set_connection=utf8mb4;//
SET collation_connection = 'utf8mb4_unicode_ci';//
drop procedure if exists erudit_INSERT_corps;
//

create procedure erudit_INSERT_corps(
    documentid int
    , erudit_xml longtext
)
begin
    declare v_row_index int unsigned;
    declare v_row_count int unsigned;
    declare v_xpath_row varchar(255);
        
    -- save off the raw xml
	insert into raw_corps(documentid, rawxml) values(documentid, erudit_xml);
    
    -- Save all raw values
	update document set corps=extractValue(erudit_xml,'/corps/text/@typetexte')
    , lang=extractValue(erudit_xml,'/corps/@lang')
    where id=documentid;
    
    commit;
end;