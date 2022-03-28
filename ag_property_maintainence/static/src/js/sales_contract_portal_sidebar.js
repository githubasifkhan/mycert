odoo.define('ag_property_maintainence.ContractPortalSidebar', function (require) {
'use strict';

var publicWidget = require('web.public.widget');
var PortalSidebar = require('portal.PortalSidebar');
var utils = require('web.utils');

publicWidget.registry.ContractPortalSidebar = PortalSidebar.extend({
    selector: '.o_portal_salescontract_sidebar',
    events: {
        'click .o_portal_salescontract_print': '_onPrintSalesContract',
    },

    /**
     * @override
     */
    start: function () {
        var def = this._super.apply(this, arguments);

        var $salescontract_html = this.$el.find('iframe#salescontract_html');
        var updateIframeSize = this._updateIframeSize.bind(this, $salescontract_html);

        $(window).on('resize', updateIframeSize);

        var iframeDoc = $salescontract_html[0].contentDocument || $salescontract_html[0].contentWindow.document;
        if (iframeDoc.readyState === 'complete') {
            updateIframeSize();
        } else {
            $salescontract_html.on('load', updateIframeSize);
        }

        return def;
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Called when the iframe is loaded or the window is resized on customer portal.
     * The goal is to expand the iframe height to display the full report without scrollbar.
     *
     * @private
     * @param {object} $el: the iframe
     */
    _updateIframeSize: function ($el) {
        var $wrapwrap = $el.contents().find('div#wrapwrap');
        // Set it to 0 first to handle the case where scrollHeight is too big for its content.
        $el.height(0);
        $el.height($wrapwrap[0].scrollHeight);

        // scroll to the right place after iframe resize
        if (!utils.isValidAnchor(window.location.hash)) {
            return;
        }
        var $target = $(window.location.hash);
        if (!$target.length) {
            return;
        }
        $('html, body').scrollTop($target.offset().top);
    },
    /**
     * @private
     * @param {MouseEvent} ev
     */
    _onPrintSalesContract: function (ev) {
        ev.preventDefault();
        var href = $(ev.currentTarget).attr('href');
        this._printIframeContent(href);
    },
});
});
