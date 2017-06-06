DELIMITER //
SET NAMES utf8mb4;//
SET CHARACTER SET utf8mb4; //
SET character_set_connection=utf8mb4;//
SET collation_connection = 'utf8mb4_unicode_ci';//
drop procedure if exists erudit_INSERT;
//

create procedure erudit_INSERT(
    documentid int
    , erudit_xml longtext
    , erudit_metadata longtext
    , erudit_biblio longtext
    , erudit_liminaire longtext
    , erudit_corps longtext
)
begin

	insert into raw_xml(documentid, rawxml) values(documentid, erudit_xml);
    
    call erudit_INSERT_entity(documentid, erudit_xml);
    call erudit_INSERT_biblio(documentid, erudit_biblio);
    call erudit_INSERT_metadata(documentid, erudit_metadata);
    call erudit_INSERT_liminaire(documentid, erudit_liminaire);
    call erudit_INSERT_corps(documentid, erudit_corps);
    
commit;
end;