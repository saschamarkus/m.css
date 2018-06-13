/*
    This file is part of m.css.

    Copyright © 2017, 2018 Vladimír Vondruš <mosra@centrum.cz>

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included
    in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE.
*/

"use strict"; /* it summons the Cthulhu in a proper way, they say */

let presenterView = null;

document.onkeydown = function(event) {
    if(event.key == 'ArrowLeft') {
        let current = document.getElementById(window.location.hash.substr(1));
        if(current) {
            let prev = current.previousElementSibling;
            if(prev && prev.id) {
                window.location.hash = '#' + prev.id;

                /* This is the main window, send the change to the presenter
                   view as well */
                if(presenterView)
                    presenterView.location.hash = '#' + prev.id;
                /* This is the presenter window, send the change to the main
                   window as well */
                else if(window.opener)
                    window.opener.location.hash = '#' + prev.id;
            }
        }
    }

    if(event.key == 'ArrowRight') {
        let current = document.getElementById(window.location.hash.substr(1));
        if(current) {
            let next = current.nextElementSibling;
            if(next && next.id) {
                window.location.hash = '#' + next.id;

                /* This is the main window, send the change to the presenter
                   view as well */
                if(presenterView)
                    presenterView.location.hash = '#' + next.id;
                /* This is the presenter window, send the change to the main
                   window as well */
                else if(window.opener)
                    window.opener.location.hash = '#' + next.id;
            }
        }
    }
}

function openPresenterView(link) {
    presenterView = window.open(link.getAttribute('href'), "presenter-view");
    return false;
}
