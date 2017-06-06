use sshcyber;

select * from document where id not in (select distinct documentid from meta) and dataset='erudit';

select * from meta;
select * from directeur;
select * from pubnum;
select * from titre;
select * from auteur;
select * from summary;
select * from motcle;
select * from biblio;
select * from note;
select * from entity;
select * from stopword;


delete from entity;
delete from meta;
delete from note;
delete from biblio;
delete from directeur;
delete from pubnum;
delete from titre;
delete from summary;
delete from auteur;
delete from motcle;
delete from raw_xml;
delete from raw_biblio;
delete from raw_liminaire;
delete from raw_corps;
delete from raw_meta;
