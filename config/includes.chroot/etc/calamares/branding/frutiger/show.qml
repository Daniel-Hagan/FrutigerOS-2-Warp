/* Frutiger OS installer slideshow (Calamares slideshow API 2) */
import QtQuick 2.0;
import calamares.slideshow 1.0;

Presentation
{
    id: presentation

    function nextSlide() { presentation.goToNextSlide(); }

    Timer {
        id: advanceTimer
        interval: 7000
        running: presentation.activatedInCalamares
        repeat: true
        onTriggered: nextSlide()
    }

    Slide { Image { anchors.fill: parent; source: "slide1.png"; fillMode: Image.PreserveAspectFit; smooth: true } }
    Slide { Image { anchors.fill: parent; source: "slide2.png"; fillMode: Image.PreserveAspectFit; smooth: true } }
    Slide { Image { anchors.fill: parent; source: "slide3.png"; fillMode: Image.PreserveAspectFit; smooth: true } }
    Slide { Image { anchors.fill: parent; source: "slide4.png"; fillMode: Image.PreserveAspectFit; smooth: true } }

    function onActivate() { presentation.currentSlide = 0; }
    function onLeave() { }
}
