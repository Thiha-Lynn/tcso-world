const menuButton = document.querySelector('.nav-toggle');
const navigation = document.querySelector('#primary-nav');

function setMenuOpen(open) {
    if (!menuButton || !navigation) return;
    menuButton.setAttribute('aria-expanded', String(open));
    menuButton.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
    navigation.classList.toggle('is-open', open);
}

menuButton?.addEventListener('click', () => {
    setMenuOpen(menuButton.getAttribute('aria-expanded') !== 'true');
});

navigation?.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => setMenuOpen(false));
});

document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && menuButton?.getAttribute('aria-expanded') === 'true') {
        setMenuOpen(false);
        menuButton.focus();
    }
});

window.matchMedia('(min-width: 981px)').addEventListener('change', (event) => {
    if (event.matches) setMenuOpen(false);
});

document.querySelectorAll('[data-current-year]').forEach((element) => {
    element.textContent = String(new Date().getFullYear());
});

const membershipForm = document.querySelector('#membership-form');
if (membershipForm) {
    const result = document.querySelector('#application-result');
    const message = document.querySelector('#application-message');
    const copyStatus = document.querySelector('#copy-status');
    const submitStatus = document.querySelector('#submission-status');
    const submitButton = document.querySelector('#submit-application');
    const consent = document.querySelector('#submission-consent');
    const payment = document.querySelector('#payment-preferences');
    let payload;
    let submitting = false;
    let submitted = false;
    const selectedPlan = () => membershipForm.querySelector('[name="plan"]:checked').value;
    const updatePlan = () => {
        const paid = selectedPlan() === 'paid';
        payment.hidden = !paid;
        payment.querySelectorAll('select').forEach(field => { field.disabled = !paid; });
        document.querySelector('#selection-summary').textContent = paid
            ? 'Paid Supporter · US$30 one-time membership fee. Includes all free benefits, 12 months of LinkedIn Premium Career and eligible partner offers. One-time community membership. Nothing charged now.'
            : 'Free Member · US$0 membership fee. Google AI Plus (12 months), Super Duolingo (12 months), Apple Music (6 months) and community resources. Activation subject to confirmation.';
    };
    const invalidate = () => {
        result.hidden = true;
        payload = null;
        submitted = false;
        consent.checked = false;
        submitButton.disabled = false;
        submitButton.textContent = 'Submit application to TCSO';
        submitStatus.textContent = '';
    };
    const setPlan = plan => {
        if (!['free', 'paid'].includes(plan) || submitting) return;
        membershipForm.querySelector(`[name="plan"][value="${plan}"]`).checked = true;
        updatePlan();
        invalidate();
    };
    setPlan(new URLSearchParams(location.search).get('plan') || 'free');
    document.querySelectorAll('[data-select-plan]').forEach(link => link.addEventListener('click', () => setPlan(link.dataset.selectPlan)));
    membershipForm.addEventListener('input', () => { updatePlan(); invalidate(); });
    membershipForm.addEventListener('change', () => { updatePlan(); invalidate(); });
    membershipForm.addEventListener('submit', event => {
        event.preventDefault();
        if (submitting || !membershipForm.reportValidity()) return;
        if (submitted) { result.scrollIntoView({behavior:'smooth', block:'start'}); return; }
        const fields = Object.fromEntries(new FormData(membershipForm));
        if (!fields.name.trim() || !fields.country.trim()) {
            const field = membershipForm.elements[!fields.name.trim() ? 'name' : 'country'];
            field.setCustomValidity('Please enter a name or country, not only spaces.');
            field.reportValidity();
            field.addEventListener('input', () => field.setCustomValidity(''), {once:true});
            return;
        }
        payload = {...fields, name: fields.name.trim(), country: fields.country.trim(), request_id: payload?.request_id || crypto.randomUUID()};
        const paid = fields.plan === 'paid';
        message.value = [
            'မင်္ဂလာပါ TCSO၊ အဖွဲ့ဝင်အဖြစ် လျှောက်ထားလိုပါသည်။',
            'Hello TCSO, I would like to apply for membership.', '',
            `Membership / အစီအစဉ်: ${paid ? 'Paid Supporter — US$30 one-time' : 'Free Member — US$0'}`,
            `Preferred name / အမည်: ${payload.name}`,
            `Country / နိုင်ငံ: ${payload.country}`,
            `Follow-up email: ${fields.contact || 'I will follow up in Messenger'}`,
            `Country coordinator: ${fields.coordinator || 'Not specified'}`,
            'Benefits requested: Google AI Plus 2 TB (12 months), Super Duolingo (12 months), Apple Music Individual (6 months), community support.',
            ...(paid ? [
                'Additional benefits: LinkedIn Premium Career (12 months) and guidance for eligible partner perks.',
                `Preferred currency: ${fields.currency}`,
                `Preferred payment method: ${fields.payment_method}`,
                'Please confirm the final amount, payment method and product eligibility for my one-time US$30 community membership before I pay.'
            ] : ['Please confirm benefit eligibility and the next steps for free membership.']),
            'No payment has been made through this form.'
        ].join('\n');
        result.hidden = false;
        copyStatus.textContent = '';
        submitStatus.textContent = 'Preview ready. Your application has not been sent yet.';
        submitStatus.classList.remove('is-error');
        result.scrollIntoView({behavior: 'smooth', block: 'start'});
        consent.focus({preventScroll:true});
    });
    submitButton.addEventListener('click', async () => {
        if (!payload || submitting || submitted) return;
        if (!consent.checked) {
            submitStatus.textContent = 'Please check the consent box before submitting, or use Messenger instead.';
            consent.focus();
            return;
        }
        submitting = true;
        submitButton.disabled = true;
        const controls = [...membershipForm.elements];
        const disabled = controls.map(control => control.disabled);
        controls.forEach(control => { control.disabled = true; });
        submitStatus.classList.remove('is-error');
        submitStatus.textContent = 'Sending your application…';
        try {
            const response = await fetch('https://myotaw.com/tcso-api/applications', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({...payload, consent:true}), signal: AbortSignal.timeout(15000)
            });
            const data = await response.json();
            if (!response.ok || !data.reference) throw new Error(data.error || 'Submission could not be confirmed.');
            submitted = true;
            message.value = `TCSO application reference: ${data.reference}\nSaved online; following up in Messenger.\n\n${message.value}`;
            submitStatus.textContent = `Application received. Reference: ${data.reference}. This is not membership approval. Copy your message and send it to TCSO in Messenger for the next steps.`;
            submitButton.textContent = 'Application received ✓';
        } catch (error) {
            submitStatus.classList.add('is-error');
            submitStatus.textContent = `We could not confirm submission. ${error.name === 'TimeoutError' ? 'The connection timed out.' : 'Please try again.'} Retrying uses the same reference request to avoid duplicates. You can also copy your application and send it through Messenger.`;
            submitButton.disabled = false;
        } finally {
            submitting = false;
            controls.forEach((control, index) => { control.disabled = disabled[index]; });
        }
    });
    const copy = async () => {
        try {
            await navigator.clipboard.writeText(message.value);
            copyStatus.textContent = 'Copied. Paste into the TCSO Messenger chat and tap Send.';
            return true;
        } catch {
            message.focus(); message.select();
            copyStatus.textContent = 'Copy the selected message manually, then open Messenger, paste and tap Send.';
            return false;
        }
    };
    document.querySelector('#copy-application').addEventListener('click', copy);
    document.querySelector('#copy-and-open').addEventListener('click', () => {
        // Open synchronously in the user gesture; noopener deliberately returns no window handle.
        window.open('https://m.me/TCSODL', '_blank', 'noopener,noreferrer');
        copy().then(ok => { if (ok) copyStatus.textContent = 'Copied. Paste and send in Messenger. If no tab opened, use “Open Messenger manually” below.'; });
    });
}
