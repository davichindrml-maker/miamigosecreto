/* Nieve de fondo y confeti. Sin librerías externas. */
(function () {
    var reducir = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // ---------- NIEVE ----------
    var lienzo = document.getElementById('nieve');
    if (lienzo && !reducir) {
        var ctx = lienzo.getContext('2d');
        var copos = [];
        var ancho = 0, alto = 0;

        function medir() {
            ancho = lienzo.width = window.innerWidth;
            alto = lienzo.height = window.innerHeight;
        }

        function nuevoCopo(arriba) {
            return {
                x: Math.random() * ancho,
                y: arriba ? -10 : Math.random() * alto,
                r: 1 + Math.random() * 3,
                v: 0.4 + Math.random() * 1.1,
                fase: Math.random() * Math.PI * 2
            };
        }

        medir();
        var cantidad = ancho < 600 ? 45 : 90;
        for (var i = 0; i < cantidad; i++) copos.push(nuevoCopo(false));
        window.addEventListener('resize', medir);

        (function dibujar() {
            ctx.clearRect(0, 0, ancho, alto);
            ctx.fillStyle = 'rgba(251,243,223,0.85)';
            for (var i = 0; i < copos.length; i++) {
                var c = copos[i];
                c.y += c.v;
                c.fase += 0.015;
                c.x += Math.sin(c.fase) * 0.6;
                if (c.y > alto + 10) copos[i] = nuevoCopo(true);
                ctx.beginPath();
                ctx.arc(c.x, c.y, c.r, 0, Math.PI * 2);
                ctx.fill();
            }
            requestAnimationFrame(dibujar);
        })();
    }

    // ---------- CONFETI ----------
    window.lanzarConfeti = function () {
        if (reducir) return;
        var cv = document.createElement('canvas');
        cv.style.cssText = 'position:fixed;inset:0;width:100%;height:100%;pointer-events:none;z-index:50';
        document.body.appendChild(cv);
        var c = cv.getContext('2d');
        var w = cv.width = window.innerWidth;
        var h = cv.height = window.innerHeight;
        var colores = ['#c8372d', '#e9b44c', '#2d6a4f', '#3a6ea5', '#fbf3df', '#e58f8f'];
        var piezas = [];
        for (var i = 0; i < 160; i++) {
            piezas.push({
                x: w / 2 + (Math.random() - 0.5) * 120,
                y: h * 0.35,
                vx: (Math.random() - 0.5) * 14,
                vy: -Math.random() * 12 - 3,
                s: 6 + Math.random() * 7,
                a: Math.random() * Math.PI,
                va: (Math.random() - 0.5) * 0.4,
                color: colores[Math.floor(Math.random() * colores.length)]
            });
        }
        var inicio = Date.now();
        (function paso() {
            var t = Date.now() - inicio;
            c.clearRect(0, 0, w, h);
            piezas.forEach(function (p) {
                p.vy += 0.28;
                p.vx *= 0.995;
                p.x += p.vx;
                p.y += p.vy;
                p.a += p.va;
                c.save();
                c.translate(p.x, p.y);
                c.rotate(p.a);
                c.fillStyle = p.color;
                c.globalAlpha = t > 3000 ? Math.max(0, 1 - (t - 3000) / 1200) : 1;
                c.fillRect(-p.s / 2, -p.s / 4, p.s, p.s / 2);
                c.restore();
            });
            if (t < 4200) requestAnimationFrame(paso);
            else cv.remove();
        })();
    };

    if (document.body.hasAttribute('data-confeti')) {
        setTimeout(window.lanzarConfeti, 350);
    }
})();
