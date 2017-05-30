DELIMITER //

drop procedure if exists erudit_INSERT_metadata;
//

create procedure erudit_INSERT_metadata(
    documentid int
    , erudit_xml text
)
begin
    declare v_row_index int unsigned;
    declare v_row_count int unsigned;
    declare v_xpath_row varchar(255);
    
    -- Save all raw values
	insert into erudit_meta (
		documentid
        , idpublic
        , ppage
        , dpage
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
        , extractValue(erudit_xml,'/admin/infoarticle/idpublic[1]/text()')
        , extractValue(erudit_xml,'/admin/infoarticle/pagination/ppage[1]/text()')
        , extractValue(erudit_xml,'/admin/infoarticle/pagination/dpage[1]/text()')
        , extractValue(erudit_xml,'/admin/revue/@id')
        , extractValue(erudit_xml,'/admin/revue/titrerev[1]/text()')
        , extractValue(erudit_xml,'/admin/revue/titrerevabr[1]/text()')
        , extractValue(erudit_xml,'/admin/revue/idissn[1]/text()')
        , extractValue(erudit_xml,'/admin/revue/idissnnum[1]/text()')
        , extractValue(erudit_xml,'/admin/numero/volume[1]/text()')
        , extractValue(erudit_xml,'/admin/numero/nonumero[1]/text()')
        , extractValue(erudit_xml,'/admin/numero/anonumero[1]/text()')
        , extractValue(erudit_xml,'/admin/numero/pub/annee[1]/text()')
        , extractValue(erudit_xml,'/admin/numero/pub/periode[1]/text()')
        , extractValue(erudit_xml,'/admin/editeur/nomorg[1]/text()')
        , extractValue(erudit_xml,'/admin/prodnum/nomorg[1]/text()')
        , extractValue(erudit_xml,'/admin/diffnum/nomorg[1]/text()')
        , extractValue(erudit_xml,'/admin/droitsauteur/nomorg[1]/text()')
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
        insert into erudit_director (
			documentid
            , fonction
            , prenom
            , nomfamille
        ) values (
			documentid
            , extractValue(erudit_xml, concat(v_xpath_row,'/fonction[1]/text()'))
            , extractValue(erudit_xml, concat(v_xpath_row,'/nompers/prenom[1]/text()'))
            , extractValue(erudit_xml, concat(v_xpath_row,'/nompers/nomfamille[1]/text()'))
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
        insert into erudit_date( 
			documentid
            , typedate
            , dt
        ) values (
			documentid
			, extractValue(erudit_xml, concat(v_xpath_row,'/@typedate'))
            , extractValue(erudit_xml, concat(v_xpath_row,'/text()'))
        );
    end while;
    
    commit;
end;