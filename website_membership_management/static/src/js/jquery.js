odoo.define('website_membership_update', function (require) {
    "use strict";

    var core = require('web.core');
    var ajax = require('web.ajax');
    var _t = core._t;


    $(document).ready(function () {

        // $(document).on('DOMSubtreeModified','.js_cart_lines',function(){
                
        //     location.reload()

        // })
        

        $('.loop').owlCarousel({
            center: false,
            
            items: 3,
            loop: false,
            margin: 0,
            merge: false,
            mergeFit: true,
            autoWidth: false,
            responsive:{
                0:{
                    items:1
                },
                600:{
                    items:2
                },
                1000:{
                    items:3 
                }
            }
          });

        $(document).on('click', '.read_more', function (ev) {
            var info=$(ev.currentTarget).siblings('p').text();
            $('.read_more_body').html(info);
            // console.log('pp')
          });


        $(document).on('click', '#renew', function () {
            var mem_id = $('.mem_id').text();
            ajax.jsonRpc('/website/membership/renew', 'call', {
                'renew': mem_id,
            })
                .then(function (data) {
                    location.reload();
                })
                .fail(function (result) {
                })
        });



        var product_id = $(".product_id").attr('value');
        $("input[name='optradio']").change(function () {
            if ($("input[name='optradio']:checked").attr('value') == 'immediate') {
                $(".membership_update_message").html("This Will Cancel the current Membership, NO AMOUNT WILL BE REFUNDED")
            }
            else {
                $(".membership_update_message").html("This Will start the new membership once the old one is expires")
            }
        });

      
        var add_to_cart = $('#add_to_cart').clone(true)
        $('.js_main_product input').on('change',function(){
            var product_id = $(".product_id").attr('value');
            var dehighligh_element=$('.active_product').removeClass('active_product');
            var highlight_element=$('[data-id='+product_id+']').addClass('active_product');
            var count = highlight_element.attr('data-counter')
            var owl = $('.owl-carousel');
            owl.owlCarousel();
            owl.trigger('to.owl.carousel', [count,500,true]);

            ajax.jsonRpc('/check/product_variant/membership', 'call', {
                'product_id': product_id,
            })
                .then(function (data) {
                    if (data == false) {
                        console.log('done')
                        $('.css_quantity').removeClass('d-none');
                        $('#membership_divs,.membership_login,.multi_membership_message,.membership_current_plan,.membership_update_message.mt-2.p-2').hide();
                        $('#add_to_cart').replaceWith('<a id="add_to_cart" class="btn btn-primary btn-lg mt8 js_check_product a-submit" href="#">Add to Cart</a>')
                        
        
                    }
                    else {
                        $('.css_quantity').addClass('d-none');
                        $('#membership_divs,.membership_login,.multi_membership_message,.membership_current_plan,.membership_update_message.mt-2.p-2').show();
                        $('#add_to_cart').replaceWith(add_to_cart)
                        
                        
                    }
                }).fail(function (result) {
        
                })
            
        });

    });
});




