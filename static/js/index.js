$(document).ready(function() {
    $("#search-keyword-container").hide();
    $("#search-keyword-home").on("input click", function() {
        var keyword = $(this).val();
        if(keyword != "") {
            $("#search-keyword-container").show();
        } else {
            $("#search-keyword-container").hide();        
        }
    });
});