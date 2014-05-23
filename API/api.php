<?php
include("simple_html_dom.php");
if (isset($_GET["letter"]))
{
    $letter = $_GET["letter"];
    $html = file_get_html("http://www.dmax.it/video/programmi/");
    $array = array();
    $i = 0;
    foreach($html->find("ol[class^=letter-" . strtolower($letter) . "]", 0)->children as $program)
    {  
       $array[$i] = $program->plaintext;
       $i++;
       }
    echo json_encode($array); 
}
else
{       
    $html = file_get_html("http://www.dmax.it/video/programmi/");
    $array = array();
    $i = 0;
    foreach($html->find('h3.section-title') as $letter) {    
        $letter = $letter->plaintext;
        $array[$i] = $letter;  
        $i++;
    }
    echo json_encode($array); 
}
?>