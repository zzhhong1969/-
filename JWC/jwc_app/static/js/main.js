$(document).ready(function() {
    // 通用初始化代码
    $('.alert').delay(3000).fadeOut('slow');

    // 表单验证
    $('form').submit(function() {
        $(this).find('button[type="submit"]').prop('disabled', true);
    });

    // 模态框处理
    $('.modal').on('shown.bs.modal', function() {
        $(this).find('[autofocus]').focus();
    });
});