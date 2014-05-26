<?php

include("simple_html_dom.php");
if (isset($_GET["letter"])) {
    $letter = $_GET["letter"];
    $html = file_get_html("http://www.dmax.it/video/programmi/");
    $array = array();

    foreach ($html->find("ol[class^=letter-" . strtolower($letter) . "]", 0)->children as $program) {
        $array[$program->plaintext] = $program->children(0)->href;
    }
    echo json_encode($array);
} else if (isset($_GET["seasons"])) {
    $show = $_GET["seasons"];
    $html = file_get_html("http://www.dmax.it/video/programmi/" . $show);
    $array = array();
    $obj = $html->find("div#seasons", 0);
    if ($obj != null) {
        $obj = $obj->find("ul", 0)->children;
        foreach ($obj as $season) {
            $array[rtrim($season->children(0)->children(0)->plaintext)] = $season->children(0)->href;
        }
        echo json_encode($array);
    } else {
        episodes("/video/programmi/" . $show, true);
    }
} else if (isset($_GET["episodes"])) {
    episodes($_GET["episodes"]);
} else if (isset($_GET["episode"])) {
    $link = $_GET["episode"];
    $html = file_get_html("http://www.dmax.it" . $link);
    $array = array();
    $array[] = $html->find("param[name^=@videoPlayer]", 0)->value;
    echo json_encode($array);
} else {
    $html = file_get_html("http://www.dmax.it/video/programmi/");
    $array = array();
    foreach ($html->find('h3.section-title') as $letter) {
        $letter = $letter->plaintext;
        $array[] = $letter;
    }
    echo json_encode($array);
}

function episodes($link, $noseason = false) {
    $html = file_get_html("http://www.dmax.it" . $link);
    $array = array();
    foreach ($html->find("ol[class^=" . ($noseason == false ? "list medium episodes" : "list medium") . "]", 0)->find("li") as $episode) {
        $obj = $episode->children(0);
        $link = $obj->href;
        $img = $obj->children(0)->src;
        $title = $obj->title;
        $duration = $obj->children(2)->plaintext;
        $desc = $obj->children(3)->children(2)->plaintext;
        $array[$title][] = $link;
        $array[$title][] = $img;
        $array[$title][] = $desc;
        $array[$title][] = $duration;
    }
    echo json_encode($array);
}

?>