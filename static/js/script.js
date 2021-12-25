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
