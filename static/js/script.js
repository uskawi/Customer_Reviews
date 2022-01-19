/*
    jQuery for MaterializeCSS initialization
*/

$(document).ready(function () {
    $(".sidenav").sidenav({edge: "left"});
});

/*
 Add the current year dynamically to copyright.
*/

$("#copyright").text(new Date().getFullYear());

/* 
 Add hover effect to search bar
*/

$("#company-name").mouseenter(function() {
    $("#company-name").css("boxShadow", "5px 10px #000");
    $("#company-name").css("background-color", "rgb(175, 248, 243)");
});

$("#company-name").mouseout(function() {
    $("#company-name").css("boxShadow", "none");
    $("#company-name").css("background-color", "#fff");
});
