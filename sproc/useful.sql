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

-- delete from entity;
-- delete from meta;
-- delete from note;
-- delete from biblio;
-- delete from directeur;
-- delete from pubnum;
-- delete from titre;
-- delete from summary;
-- delete from auteur;
-- delete from motcle;
-- delete from raw_xml;
-- delete from raw_biblio;
-- delete from raw_liminaire;
-- delete from raw_corps;
-- delete from raw_meta;

/* alter table frenchngram add column wordtype varchar(20);
alter table frenchngram add column raw varchar(200);

update frenchngram 
set raw=substring_index(word, '_', 1)
, wordtype=substring_index(word, '_', -1)
where LENGTH(word) - LENGTH(REPLACE(word, '_', '')) = 1;

update frenchngram 
set raw=substring_index(word, '_', 1)
, wordtype=substring_index(word, '_', -1)
where LENGTH(word) - LENGTH(REPLACE(word, '_', '')) = 2
and substring_index(word, '_', 1) = replace(substring_index(word, '_', 2), '_', '')
and wordtype is null;

update frenchngram 
set raw=substring_index(word, '_', 2)
, wordtype=substring_index(word, '_', -1)
where LENGTH(word) - LENGTH(REPLACE(word, '_', '')) = 2
and wordtype is null; */

select word
, substring_index(word, '_', 1)
, substring_index(word, '_', 2)
, substring_index(word, '_', -1)
from frenchngram 
where LENGTH(word) - LENGTH(REPLACE(word, '_', '')) = 2
and wordtype is null;

select word
, substring_index(word, '_', 1)
, substring_index(word, '_', 2)
, substring_index(word, '_', -1)
from frenchngram 
where LENGTH(word) - LENGTH(REPLACE(word, '_', '')) = 3
and wordtype is null;

select word
, substring_index(word, '_', 1)
, substring_index(word, '_', 2)
, substring_index(word, '_', -1)
from frenchngram 
where LENGTH(word) - LENGTH(REPLACE(word, '_', '')) = 2
and substring_index(word, '_', 1) = replace(substring_index(word, '_', 2), '_', '');

-- select oht.wordoed
-- , oht.fr_translation
-- , oht.label
-- , oht.pos
-- , h.id 
-- from oht
-- left join heading h on h.fr_heading=oht.fr_heading and h.catid=oht.catid
-- INTO OUTFILE 'C://ProgramData//MySQL//MySQL Server 5.7//Uploads//temp.csv'
-- FIELDS TERMINATED BY ','
-- ENCLOSED BY '"'
-- LINES TERMINATED BY '\n';
-- 
-- LOAD DATA INFILE 'C://ProgramData//MySQL//MySQL Server 5.7//Uploads//temp.csv' INTO TABLE word
-- FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' (@wordoed, @fr_translation, @label, @pos, @headingid) 
-- set word=@wordoed, fr_translation=@fr_translation, label=@label, pos=@pos, headingid=@headingid;

-- delete from topic; delete from term; delete from topicterm; delete from doctopic; delete from userdoctopic; delete from dochash; delete from headingterm;

select t.*, h.heading, th.thematicheading from topic t
left join heading h on h.id=t.headingid
left join thematicheading th on th.id=h.thematicheadingid
order by h.heading

select * from headingterm order by topicid desc
select distinct lower(word) word from stopword where dataset='adam2' order by word

select topicid, max(dist)
from topicterm
group by topicid

select * from topic

select * from term t 
left join word w on lower(w.fr_translation)=t.word
left join word w2 on lower(w2.word)=t.word
where w.id is null 
and w2.id is null
order by t.word

select * from dochash
select * from doctopic
select * from userdoctopic
select * from document where id=85093
select * from oht


select * from term t order by word
-- update term t
left join pos p on p.pos=t.pos
-- set t.oht=p.oht


select * from stopword order by word

(?<=")(?:\\.|[^"\\])*(?=")