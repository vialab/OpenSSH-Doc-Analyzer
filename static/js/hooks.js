/******************************************************************************
 * hooks.js
 * Ajax calls that connect us to the database
 * * Last updated: 07/01/2018
 *****************************************************************************/

// get journal distribution of erudit
function getJournalCount( data, merge_chart=true ) {
    let post_data = JSON.stringify([{"keyword_list": []}]);
    if(typeof(data) != "undefined" && data != null) {
        post_data = JSON.stringify(data);
    }
    // created a timeout for this hook so that the vis is not
    // regenerated every time when adding/removing multiple search items
    if(journal_timeout) {
        clearTimeout(journal_timeout);
    }
    journal_timeout = setTimeout(function() {
        $.ajax({
            url: "erudit/journal_count"
            , contentType: "application/json"
            , data: post_data
            , dataType: "json"
            , type: "POST"
            , success: function(data) {
              drawJournalCount(data, merge_chart, journal_count_minimized);
            }
        });
    }, 500);
}

// get the current search terms in a json format
function getSearchTerms(only_words=false) {
    let keyword_list = [];
    $("#search-term-box .term-container").each(function(i) {
        let k = $(".custom-keyword-heading", $(this)).html().toLowerCase();
            k = k.normalize('NFD').replace(/[\u0300-\u036f]/g, "");
        if(only_words) {
            keyword_list.push(k);
            return;
        }
        if($(this).hasClass("custom-keyword")) {
            keyword_list.push( {
                "heading_id": $(".custom-keyword-heading", $(this)).attr("heading-id"),
                "keyword": k,
                "term_id": $(this).data("termid"),
                "weight": $(".custom-keyword-weight", $(this)).val()-1,
                "order": i+1,
                "must_include": $(".star", $(this)).hasClass("active")
            });
        }
    });
    return keyword_list;
}

// fetch a previously used set of search terms and search again
function recoverSearch(search_id) {
    $.ajax({
        url: "recoversearch/" + search_id
        , type: "GET"
        , contentType: "application/json"
        , success: function(content) {
            let tiers = content["tier_index"];
            home_tier = tiers.home;
            parent_tier = tiers.parent;
            child_tier = tiers.child;
            let data = content["content"];
            console.log(data);
            for(let i = 0; i < data.length; i++) {
                drawKeyword(data[i].keyword, data[i].heading_id, data[i].tier_index, false, data[i].term_id);
            }
            search(search_id);
        }
    });
}

// fetch keyword list from server and display results
function getKeywordList(keyword, cb_keyword) {
    $.ajax({
        url: "searchkeyword"
        , contentType: "application/json"
        , data: JSON.stringify({ "data":keyword })
        , dataType: "json"
        , type: "POST"
        , success: function(data) {
            showKeywordResults(data, cb_keyword);
        }
    });
}

// what happens when a keyword is clicked in search dialog vis
function headingClicked(d, quick_search=false) {
    if(d.data.heading_id == "root") return;
    $.ajax({
        type: "GET"
        , url: "/oht/synset/" + d.data.heading_id
        , success: function(response) {
            // clear modal
            $(".word-box #heading-words", ".part-of-speech h4", "").html("");
            populateBOW(response.words, quick_search);
            populatePOS(response.pos, "n");
            // set title and go
            $(".part-of-speech h4").html(response.name);
            $("#modal-tier-index").val(response.tierindex);
            $("#modal-heading-id").val(d.data.heading_id);
        }
    });
}

// get the words within selected heading
function getSynset(elem, heading_id) {
    $(".pos-container").removeClass("active");
    $(elem).addClass("active");
    $.ajax({
        type: "GET"
        , url: "/oht/synset/" + heading_id
        , success: function(response) {
            // write the words onto the screen
            populateBOW(response.words, false);
        }
    });
}

// what happens when a heading is selected to be the main node
function reorderVis() {
    $.ajax({
        type:"GET"
        , url: "/oht/tier/" + $("#modal-tier-index").val()
        , success: function(data) {
            home_tier = data.home;
            parent_tier = data.parent;
            child_tier = data.child;
            $("#add-term").click();
        }
    });
}

// query and update search results
function getSearchResults( data ){
  $("#loading").show();
    $.ajax({
        url: "search"
        , contentType: "application/json"
        , data: JSON.stringify(data)
        , dataType: "json"
        , type: "POST"
        , success: function(data) {
          $("#loading").hide();
            showSearchResults(data);
            updateJournalCount();
            $(".new-search-term").removeClass("new-search-term");
            $(".star.new").removeClass("new");
            $(".star.old").removeClass("old");
        }
    });
}

// view all the keywords that we have saved for a single document
function showDocumentKeywords(doc_id, doc_title) {
    $("#see-all-modal .modal-title").html(doc_title);
    $.ajax({
        type:"GET"
        , url: "/document/keywords/" + doc_id
        , success: function(data) {
            let search_Terms = getSearchTerms(true);
            let $list = $("<ul class='doc-term'></ul>");
            for(y in data) {
                let topic = data[y];
                let html = "<li><a id='" + topic.id + "' onclick='drawKeyword(\""
                + topic.name+ "\",\""+ topic.heading_id + "\",\"" + topic.tier_index
                +  "\", true, \"" + topic.id + "\");' data-keyword='"
                + topic.name + "' class='search-term";
                if($.inArray(topic.name,search_terms) != -1) {
                    html += " existent";
                }
                html += "'>" + topic.rank + ". "+ topic.name + "</a></li>";
                $list.append(html);
            }
            $("#see-all-modal .modal-body").html($list);
            $("#see-all-modal").modal("show");
        }
    });
}
