DELIMITER //

drop procedure if exists sp_systemerror;
//

create procedure sp_systemerror(
    errormsg blob
)
begin

insert into systemerror(msg) values(errormsg);
commit;

end;