let searching = true, peeking = false, keyword_searching = true; // toggle modes
let target = ""; // retain which element we are editting
let target_parent = ""; // element parent
let target_index = ""; // element tier index
let type_timeout; // interval that listens for last keypress
let vis_width = $("#search-dialog-main").width();
let last_heading = "";
let selected_heading = "";
// d3 does not support jquery.click() events for some reason
jQuery.fn.d3click = function () {
    this.each(function (i, e) {
        var evt = new MouseEvent("click");
        e.dispatchEvent(evt);
    });
};

// whenever a vis is clicked, open up our search dialog
$(document).on("click", ".term-vis svg", function() {
    let $parent = $(this).parent().parent();
    // deselect all other svgs
    $(".term-container").removeClass("selected");
    // select the one we just clicked
    $parent.addClass("selected");
    // insert heading title
    $("#search-dialog-title").html($(".term-heading", $parent).html());
    
    // toggle search dialog
    if(!searching) {
        toggleSearchDialog();
    }
    
    target = $(this).attr("id");
    target_parent = $(this).parent().attr("id");
    target_index = $(this).attr("tier-index");
    // draw vis of current tier in search dialog
    let vis_height = $(window).height()-$("#search-term-container").height();
    let heading_id = $(".term-heading-id", $parent).val();
    selected_heading = heading_id;
    createNewVis("#search-dialog", "search-dialog-vis", "/oht/"
        , target_index, vis_width, vis_height, headingClicked);

    // set up the weight slider bar to match selection
    let weight = $(".term-heading-weight", $parent).val();
    setWeightValue(weight);
    $("#search-dialog .slider").css("bottom"
        , $("#search-term-container").height() + 15);
});

// avail previous document results during search
$("#search-result-container").on("click", function() {
    if(peeking) {
        toggleSearchDialog();
    } else {
        togglePeek();    
    }
});
// peek at the current search results
$("#search-dialog").on("click", function() {
    if(peeking) togglePeek();
});

// add a new term
$("#add-term").on("click", function() {
    // draw vis of current tier in search dialog
    let vis_height = $(window).height()-$("#search-term-container").height()-120;
    d3.select("#search-dialog-vis").remove();
    d3.select("#search-dialog-vis-parent").remove();
    d3.select("#search-dialog-vis-child").remove();
    createNewVis("#search-dialog-main", "search-dialog-vis-parent", "/oht/"
        , home_tier, vis_width, vis_height, headingClicked);
    searching = false;
    selected_heading = "";
    toggleSearchDialog();
});

// if we resize the screen, close the search dialog and adjust elements
$(window).on("resize", function() {
    searching = true;
    keyword_searching = true;
    toggleSearchDialog();
    toggleKeywordDialog();
});

$("#search-keyword, #search-keyword-home").on("input click", function() {
    let keyword = $(this).val();
    $(".no-keyword").hide();    
    if(!keyword_searching) {
        if(keyword != "") {
            toggleKeywordDialog();
        } else {
            return;
        }
    } else {
        if(keyword == "") {
            toggleKeywordDialog();
            return;
        }
    }
    setKeyword(keyword);    
    // wait one second until after the person is done typing
    // before running the request
    $(".load-keyword").show();
    if(type_timeout) {
        $("#search-keyword-container .keyword-container").remove();
        clearTimeout(type_timeout);
    }

    let cb_keyword = function() {
        let heading_id = $(this).attr("heading-id");
        openExploreVis(heading_id);
    };
    
    if($(this).attr("id") == "search-keyword-home") {
        cb_keyword = function() {
            window.location.href = "/analyzer?quicksearch=" 
                + $(".keyword-heading", this).html() + "&headingid="
                + $(this).attr("heading-id") + "&tierindex="
                + $(this).attr("tier-index");
        };
    }

    type_timeout = setTimeout(function() {
        getKeywordList(keyword, cb_keyword);
    }, 1000);
});

$(document).keyup(function(e) {
    // doesn't matter if search dialog closed
    if(!searching && !keyword_searching && journal_count_minimized) {        
        return;
    }
    if (e.keyCode === 27) { // ESC key
        if(!journal_count_minimized) {
            redrawJournalCount(true);
            return;
        }
        if(searching) {
            toggleSearchDialog();
        }
        if(keyword_searching) {
            toggleKeywordDialog();
        }
    }
});

$(document).ready(function() {
    toggleKeywordDialog();
    toggleSearchDialog();
    // instantiate drag and drop elems
    $("#search-term-box").sortable({
        items: ".term-container"
    });
    $("#modal-synset").modal({show:false});
    $("#weight-slider").slider();
    let search_id = getParameterByName("searchid");
    let quick_search = getParameterByName("quicksearch");
    let heading_id = getParameterByName("headingid");
    let tier_index = getParameterByName("tierindex");
    if(quick_search) { 
        if(heading_id) {
            openExploreVis(heading_id);
        } else {
            drawKeyword(quick_search, "");
        }
    } else if(search_id) {
        recoverSearch(search_id);
        return;
    }
    updateJournalCount();
});


function getOhtDirectory(heading_id=181456) {
    $.ajax({
        url: "oht/directory/" + heading_id
        , type: "GET"
        , contentType: "application/json"
        , success: function(data) {
            
        }
    });
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
            for(let i = 0; i < data.length; i++) {
                // let weight = parseInt(data[i].weight);
                if(data[i].keyword) {
                    drawKeyword(data[i].keyword, data[i].heading_id, false, data[i].term_id);
                } else {
                    drawSearchTerm(data[i].tier_index
                        , data[i].heading_id, data[i].heading, weight);
                }
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

// display a set of keywords in keyword dialog
function showKeywordResults(data, cb_keyword) {
    $(".load-keyword").hide();
    if(data.length == 0) {
        $(".no-keyword").show();    
    }
    for(i in data) {
        let clean_tier_index = data[i][4].replace(/\./g, "-");
        let svg_path = "keyword-vis-" + clean_tier_index;
        svg_path += "-" + $("[id^=" + svg_path + "]").length.toString();
        // create the container and add to dom
        let $box = $("<div class='keyword-container' id='keyword-" 
                + clean_tier_index + "' tier-index='" + data[i][4] 
                +"' heading-id='" + data[i][0] + "'>\
            <div class='keyword-heading'>" + data[i][2] + "</div>\
            <div class='keyword-vis' id='" + svg_path + "'></div>\
        </div>");
        $(".custom-keyword-container").after($box);
    }
    $(".custom-keyword-container").off("click");
    $(".custom-keyword-container").on("click", function() {
        drawKeyword($(".keyword-heading").html(),"",true);
        toggleKeywordDialog();
    });
    
    $(".custom-keyword-container.homepage").on("click", function() {
        $(this).off("click");
        window.location.href = "/analyzer?quicksearch=" + $(".keyword-heading", this).html();
    });

    $(".keyword-container").on("click", cb_keyword);
}

// set custom keyword option in keyword dialog
function setKeyword(keyword) {
    $("#search-keyword-container .keyword-heading").html(keyword);
}

// delete a search term from dom
function deleteTerm(e) {
    $(e).parent().remove();
    if(searching) {
        toggleSearchDialog();
    }
    updateJournalCount(true);
    window.event.cancelBubble = true;
}

// open or close keyword search dialog
function toggleKeywordDialog() {
    if(keyword_searching) {
        $("#search-keyword-dialog").css("left", -$(window).width()-75);
        keyword_searching = false;
        $("#search-keyword-box").hide();
        $("#search-keyword").val("");
    } else {
        if(searching) {
            toggleSearchDialog();
        }
        $("#search-keyword-box").show();
        $("#search-keyword-dialog").css("left", 0);
        keyword_searching = true;
    }
}

// open or close the search dialog
function toggleSearchDialog() {
    if(searching) {
        $("#journal-count").css({
            "right": journal_count_margin
        });
        // need to close
        $("#search-dialog").css("left", -$(window).width()-75);
        $("#search-result-container").css({
            "left": 0,
            "width": "100vw",
            "padding-left": "2%",
            "padding-right": "2%"
        });
        $("#search-dialog svg").css("padding-left", 0);
        $("#search-dialog-title").css("margin-left", 0);
        $("#search-dialog .slider").css("margin-left", 0);
        searching = false;
        peeking = false;
        $(".term-container").removeClass("selected");
        $("#search-keyword-box").hide();
    } else {
        if(!journal_count_minimized) {
            redrawJournalCount(true);
        }
        $("#journal-count").css({
            "right": -($(window).width()*journal_size_ratio)+journal_count_margin
        });
        if(keyword_searching) {
            toggleKeywordDialog();
        }
        toggleCarousel();
        // need to open
        $("#search-dialog").css("left", 0);
        $("#search-result-container").css({
            "left": $("#search-dialog").width(),
            "width": "30vw",
            "padding-left": "0",
            "padding-right": "0"
        });
        searching = true;
        $("#search-keyword-box").show();
    }
}

// instantiate slick carousel
function toggleCarousel() {
    try { $('#search-carousel').slick("unslick"); } catch(e) {}
    $('#search-carousel').slick({
        centerMode: true,
        centerPadding: '60px',
        slidesToShow: 3,
        responsive: [
        {
            breakpoint: 768,
            settings: {
            arrows: true,
            centerMode: true,
            centerPadding: '40px',
            slidesToShow: 3
            }
        },
        {
            breakpoint: 480,
            settings: {
            arrows: true,
            centerMode: true,
            centerPadding: '40px',
            slidesToShow: 1
            }
        }
        ]
    });
}

// Toggle document result view during search
function togglePeek() {
    if(searching) {
        // only relevant when search dialog is open
        let result_offset = $(window).width()-$("#search-result-container").width();
        let search_offset = ($("#search-dialog").width()+$("#search-result-container").width()) - $(window).width();
        if(!journal_count_minimized) redrawJournalCount(true);
        if(peeking) {
            // need to close
            $("#search-dialog").css("left", 0);
            $("#search-dialog svg").css("padding-left", 0);
            $("#search-dialog-title").css("margin-left", 0);
            $("#search-dialog .slider").css("margin-left", 0);
            $("#search-result-container").css("left", $("#search-dialog").width());
            $("#journal-count").css({
                "right": -($(window).width()*journal_size_ratio)+journal_count_margin
            });
            peeking = false;
        } else {
            // need to open
            $("#search-dialog").css("left", -(search_offset));
            $("#search-dialog svg").css("padding-left", search_offset/2);
            $("#search-dialog-title").css("margin-left", search_offset/2);
            $("#search-dialog .slider").css("margin-left", search_offset/2);
            $("#search-result-container").css("left", result_offset);
            $("#journal-count").css({
                "right": journal_count_margin
            });
            peeking = true;
        }
    }
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


// populate pos for this heading onto vis
function populatePOS(data, selected_pos) {
    $(".part-of-speech #pos-words").html("");
    for(let i = 0; i < data.length; i ++) {
        let html = "<div class='pos-container";
        if(selected_pos == data[i].pos) {
            html += " active";
        }
        if(parseInt(data[i].size) == 0) {
            html += " empty'";
        } else {
            html += "' onclick='getSynset(this, \"" + data[i].id + "\");'"
        }
        html += ">";
        html += data[i].pos + ". " + data[i].name + " (" + data[i].size + ")";
        html += "</div>";
        $(".part-of-speech #pos-words").append(html);
    }
}

// populate bag of words for this heading onto vis
function populateBOW(data, quick_search) {
    $(".word-box #heading-words").html("");
    $(".search-side #heading-words").height($(window).height() 
        - $(".search-side.part-of-speech").height() - 330);
    $(".search-side.part-of-speech #pos-words").css("max-height", $(window).height() * 0.3);
    // add new keywords from synset
    for(let i = 0; i < data.length; i ++) {
        let html = "<div class='bow-word text-center";
        if(data[i]["enable"]) {
            if(quick_search) {
                html += "' onclick='window.location.href=\"/analyzer?quicksearch=" + data[i]["id"] + "\"');'";
            } else {
                html += "' onclick='drawKeyword(\"" + data[i]["name"] + "\", \"" + data[i]["heading_id"] + "\", true, \""+data[i]["enable"]+"\");'";
            }
        } else {
            html += " no-click'";
        }
        html += ">" + data[i]["name"] + "</div>";
        $(".word-box #heading-words").append(html);
    }
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

// what happens when a keyword is clicked in search dialog vis
function keywordClicked(d) {
    let new_tier_index = d.data.parent;
    let $target = $("#"+target, "#"+target_parent);
    let $container = $target.parent().parent();
    let weight = ($("#weight-slider").val()-1) * 0.25;
    let vis_size = min_size + (add_size * weight);
    
    // save relevant identifiers to dom for later
    saveSelection($container, d.data.heading_id
        , $("#weight-slider").val(), d.data.name);

    // draw the mini-vis to the dom element
    createNewVis("#search-term-box #"+target_parent, target, "/oht/"
        , new_tier_index, vis_size, vis_size);

    $target.attr("tier-index", new_tier_index);

    // highlight what was just changed for visual feedback
    animate("select", $("#"+target_parent).parent());
}

// make sure relevant search items are saved to dom
function saveSelection($container, heading_id, weight, name) {
    $(".term-heading-id", $container).val(heading_id);
    $(".term-heading-weight", $container).val(weight);
    $(".term-heading", $container).html(name);
}

// take saved dom elements and get new document results
function search(search_id) {
    let keyword_list = getSearchTerms();
    if(keyword_list.length == 0) return;
    
    let data = { "keyword_list":keyword_list };
    if(search_id) data["search_id"] = search_id;

    getSearchResults(data);
    updateJournalCount();
}

// query and update search results
function getSearchResults( data ){
    $.ajax({
        url: "search"
        , contentType: "application/json"
        , data: JSON.stringify(data)
        , dataType: "json"
        , type: "POST"
        , success: function(data) {
            showSearchResults(data);
            $(".new-search-term").removeClass("new-search-term");
            $(".star.new").removeClass("new");
            $(".star.old").removeClass("old");
        }
    });
}

// format and display search results
function showSearchResults( data ) {
    $("#search-result-container .doc").remove();    
    if(data.length == 0) {
        let $format = $("<div class='doc'>Sorry, no search results found.</div>");
        $("#search-result-container").append($format);
        return;        
    }
    search_terms = getSearchTerms(true);
    for(i in data) {
        let $format = $("<div class='doc'> \
            <h3>ARTICLE</h3>\
            <div class='doc-title'></div>\
            <div class='doc-author'></div>\
            <div class='doc-cite'></div>\
            <h3>MOTS CLÉS</h3>\
            <ul class='doc-term' id='doc-topic'></ul>\
        </div>");

        let doc = data[i];
        $format.attr("id", doc.id);
        $("#search-result-container").append($format);
        let $container = $(".doc#" + doc.id);
        $(".doc-title", $container).html( doc.title );
        $(".doc-author", $container).html( doc.author );
        $(".doc-cite", $container).html( doc.citation );

        // insert topics
        let n = 0;
        for(y in doc.topiclist) {
            let topic = doc.topiclist[y];
            if(topic.dist < 0.1) continue;
            let dist = topic.dist * 100;
            // let $docterm = $("<li><a id='" + topic.id 
            //     + "' onclick='drawSearchTerm(\"" + topic.tier_index 
            //     + "\", \"" + topic.heading_id + "\",\"" + topic.heading 
            //     + "\");' class='search-term'>" + topic.thematicheading 
            //     + " | " + topic.heading + " ( " + dist.toFixed(2) 
            //     + " % )</a></li>");
            let html = "<li><a id='" + topic.id + "' onclick='drawKeyword(\"" 
            + topic.name+ "\",\""+ topic.heading_id + "\", true, \"" 
            + topic.id + "\");' data-keyword='" 
            + topic.name + "' class='search-term";
            if(topic.is_keyword || $.inArray(topic.name,search_terms) != -1) {
                topic.is_keyword = 1;
                html += " existent";
            }
            html += "'>" + (++n) + ". "+ topic.name 
            + "</a></li>";
            let $docterm = $(html);
            $("#doc-topic", $container).append($docterm);
        }
        let has_keywords = false;
        let has_missing = false;
        let last_rank = 5;
        let list_id = "#doc-topic";
        let top_keywords = [];
        $.each($("#doc-topic a", $container), function() {
            top_keywords.push($(this).data("keyword"));
        })
        for(y in doc.keywordlist) {
            let topic = doc.keywordlist[y];
            let html = "<li><a id='" + topic.id + "' class='search-term ";
            if($.inArray(topic.name, top_keywords) != -1) continue;
            if(topic.rank) {
                if(!has_keywords) {
                    has_keywords = true;
                }
                html = "<li>";
                if((topic.rank - last_rank) > 1) html += "<span>...</span>";
                html += "<a id='" + topic.id + "' class='search-term ";
                html += "existent' onclick='forceIncludeTerm(\"" + topic.name + "\", \"" 
                + topic.heading_id + "\", \"" + topic.id + "\");'>" + (topic.rank) + ". ";
                last_rank = topic.rank;
            } else {
                if(!has_missing) {
                    $(list_id, $container).append("<li><a class='see-all-terms' \
                    onclick='showDocumentKeywords(\"" + doc.id + "\",\"" + doc.title
                    + "\");'>voir tout &raquo;</a></li>")
                    has_missing = true;
                    $container.append($("<h3>TERMES MANQUANTS</h3><ul class='doc-term' id='doc-missing-term'></ul>"));
                    list_id = "#doc-missing-term";
                }
                html += "non-existent' onclick='forceIncludeTerm(\"" + topic.name + "\", \"" 
                + topic.heading_id + "\", \"" + topic.id + "\");'>"
            }
            html += topic.name + "</a></li>";
            $(list_id, $container).append($(html));
        }
    }
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
                + topic.name+ "\",\""+ topic.heading_id + "\", true, \"" 
                + topic.id + "\");' data-keyword='" 
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

// force the inclusion of a term (i.e. toggle its star ON)
function forceIncludeTerm(keyword, heading_id, id) {
    let already_used = false;
    $("#search-term-box .term-container").each(function(i) {
        let used_keyword = $(".custom-keyword-heading", $(this)).html()
        if(keyword == used_keyword) {
            already_used = true;
            $.each($(".star", $(this)), function() {
                toggleStar(this);
            });
        }
    });
    if(!already_used) {
        drawKeyword(keyword, heading_id, true, id);
    }
    updateJournalCount(true);
}

// handle animations here so we can reuse
function animate(animation, $target) {
    switch(animation) {
        case "select":
            // highlight this box for visual feed back of changes
            $target.removeClass("selected");        
            $target.addClass("changed");
            setTimeout(function() {
                $target.removeClass("changed");
            }, 500);
            break;
    }
}

// open up the exploration tool at a specific heading
function openExploreVis(heading_id) {
    if(heading_id == selected_heading) return;
    home_tier = heading_id;
    $("#add-term").click();
    if(heading_id != selected_heading) {
        last_heading = selected_heading;
        selected_heading = heading_id;
    } 
    headingClicked({"data":{"heading_id":heading_id}});
}

// update the journal count vis
function updateJournalCount(merge=false) {
    let keyword_list = getSearchTerms();
    if(keyword_list.length > 0) {
        getJournalCount({"keyword_list":keyword_list}, merge);
    }
}
