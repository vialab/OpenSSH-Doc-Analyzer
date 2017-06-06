DELIMITER //
SET NAMES utf8mb4;//
SET CHARACTER SET utf8mb4; //
SET character_set_connection=utf8mb4;//
SET collation_connection = 'utf8mb4_unicode_ci';//
drop procedure if exists erudit_INSERT_metadata;
//

create procedure erudit_INSERT_metadata(
    documentid int
    , erudit_xml longtext
)
begin
    declare v_row_index int unsigned;
    declare v_row_count int unsigned;
    declare v_xpath_row varchar(255);
        
    -- save off the raw xml
	insert into raw_meta(documentid, rawxml) values(documentid, erudit_xml);
    
    -- Save all raw values
	insert into meta (
		documentid
        , idpublic
        , ppage
        , dpage
        , nbrefbiblio
        , revueid
        , titrerev
        , titrerevabr
        , idissn
        , idissnnum
        , volume
        , nonumero
        , anonumero
        , annee
        , periode
        , editeur
        , prodnum
        , diffnum
        , droitsauteur
    ) values (
		documentid
        , extractValue(erudit_xml,'/admin/infoarticle/idpublic[1]//text()')
        , extractValue(erudit_xml,'/admin/infoarticle/pagination/ppage[1]//text()')
        , extractValue(erudit_xml,'/admin/infoarticle/pagination/dpage[1]//text()')
        , extractValue(erudit_xml,'/admin/infoarticle/nbrefbiblio//text()')
        , extractValue(erudit_xml,'/admin/revue/@id')
        , extractValue(erudit_xml,'/admin/revue/titrerev[1]//text()')
        , extractValue(erudit_xml,'/admin/revue/titrerevabr[1]//text()')
        , extractValue(erudit_xml,'/admin/revue/idissn[1]//text()')
        , extractValue(erudit_xml,'/admin/revue/idissnnum[1]//text()')
        , extractValue(erudit_xml,'/admin/numero/volume[1]//text()')
        , extractValue(erudit_xml,'/admin/numero/nonumero[1]//text()')
        , extractValue(erudit_xml,'/admin/numero/anonumero[1]//text()')
        , extractValue(erudit_xml,'/admin/numero/pub/annee[1]//text()')
        , extractValue(erudit_xml,'/admin/numero/pub/periode[1]//text()')
        , extractValue(erudit_xml,'/admin/editeur/nomorg[1]//text()')
        , extractValue(erudit_xml,'/admin/prodnum/nomorg[1]//text()')
        , extractValue(erudit_xml,'/admin/diffnum/nomorg[1]//text()')
        , extractValue(erudit_xml,'/admin/droitsauteur/nomorg[1]//text()')
	);

    -- Save all related directors of this journal
    set v_row_count := extractValue(erudit_xml,'count(/admin/revue/directeur)');
	set v_row_index := 0;
    -- loop through all the row elements
    while v_row_index < v_row_count do        
        set v_row_index := v_row_index + 1;
        set v_xpath_row := concat(
            '/admin/revue/directeur['
        ,   v_row_index
        ,   ']'
        );
        insert into directeur (
			documentid
            , fonction
            , prenom
            , autreprenom
            , nomfamille
            , suffixe
        ) values (
			documentid
            , extractValue(erudit_xml, concat(v_xpath_row,'/fonction[1]//text()'))
            , extractValue(erudit_xml, concat(v_xpath_row,'/nompers/prenom[1]//text()'))
            , extractValue(erudit_xml, concat(v_xpath_row,'/nompers/autreprenom[1]//text()'))
            , extractValue(erudit_xml, concat(v_xpath_row,'/nompers/nomfamille[1]//text()'))
            , extractValue(erudit_xml, concat(v_xpath_row,'/nompers/suffixe[1]//text()'))
        );
    end while;
    
    -- Save all relevant publication dates
    set v_row_count := extractValue(erudit_xml,'count(/admin/numero/pubnum/date)');
	set v_row_index := 0;
    -- loop through all the row elementserudit_metaerudit_meta
    while v_row_index < v_row_count do        
        set v_row_index := v_row_index + 1;
        set v_xpath_row := concat(
            '/admin/numero/pubnum/date['
        ,   v_row_index
        ,   ']'
        );
        insert into pubnum( 
			documentid
            , typedate
            , dt
        ) values (
			documentid
			, extractValue(erudit_xml, concat(v_xpath_row,'/@typedate'))
            , extractValue(erudit_xml, concat(v_xpath_row,'//text()'))
        );
    end while;
    
    commit;
end;