function quickFilter(type) {
    let url = new URL(window.location.href);

    if (type === 'cheap') {
        url.searchParams.set('cheap', '1');
    }

    if (type === 'fast') {
        url.searchParams.set('time', '30');
    }

    window.location.href = url;
}