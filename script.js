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
const membershipPlan = document.querySelector('#membership-plan');
const applicationResult = document.querySelector('#application-result');
const applicationMessage = document.querySelector('#application-message');
const copyApplication = document.querySelector('#copy-application');
const copyAndOpen = document.querySelector('#copy-and-open');
const copyStatus = document.querySelector('#copy-status');
const paymentPreferences = document.querySelector('#payment-preferences');

if (membershipForm && membershipPlan && applicationResult && applicationMessage) {
    const requestedPlan = new URLSearchParams(window.location.search).get('plan');
    if (requestedPlan === 'paid' || requestedPlan === 'free') membershipPlan.value = requestedPlan;

    const updatePaymentPreferences = () => {
        if (paymentPreferences) paymentPreferences.hidden = membershipPlan.value !== 'paid';
    };
    updatePaymentPreferences();
    membershipPlan.addEventListener('change', updatePaymentPreferences);

    document.querySelectorAll('[data-select-plan]').forEach((link) => {
        link.addEventListener('click', () => {
            const plan = link.getAttribute('data-select-plan');
            if (plan === 'paid' || plan === 'free') membershipPlan.value = plan;
        });
    });

    membershipForm.addEventListener('submit', (event) => {
        event.preventDefault();
        if (!membershipForm.reportValidity()) return;

        const fields = new FormData(membershipForm);
        const isPaid = fields.get('plan') === 'paid';
        const plan = isPaid ? 'PAID SUPPORTER MEMBER — US$30' : 'FREE MEMBER — US$0';
        const coordinator = fields.get('coordinator') || 'No preference stated / မရွေးချယ်ရသေးပါ';
        const message = [
            'မင်္ဂလာပါ TCSO၊ အဖွဲ့ဝင်အဖြစ် လျှောက်ထားလိုပါသည်။',
            'Hello TCSO, I would like to apply for membership.',
            '',
            `ရွေးချယ်ထားသော အစီအစဉ် / Membership plan: ${plan}`,
            `အမည် / Preferred name: ${String(fields.get('name')).trim()}`,
            `လက်ရှိနေထိုင်ရာနိုင်ငံ / Country of residence: ${String(fields.get('country')).trim()}`,
            `နိုင်ငံတာဝန်ခံအဖြစ် ပါဝင်လိုမှု / Country coordinator interest: ${coordinator}`,
            ...(isPaid ? [`ငွေကြေး / Preferred currency: ${fields.get('currency')}`, `ပေးချေမှုနည်းလမ်း / Preferred method: ${fields.get('payment_method')}`] : []),
            '',
            isPaid
                ? 'ငွေပေးချေမီ အဖွဲ့ဝင်ကာလ၊ နောက်ဆုံးငွေပမာဏနှင့် အသုံးပြုနိုင်သော ပေးချေမှုနည်းလမ်းကို အတည်ပြုပေးပါ။\nPlease confirm the membership period, final amount and supported payment method before I pay.'
                : 'အခမဲ့အဖွဲ့ဝင် လျှောက်ထားမှုအတွက် နောက်တစ်ဆင့်ကို လမ်းညွှန်ပေးပါ။\nPlease share the next steps for my free membership application.'
        ].join('\n');

        applicationMessage.value = message;
        applicationResult.hidden = false;
        copyStatus.textContent = '';
        copyApplication.textContent = 'Copy message';
        if (copyAndOpen) copyAndOpen.textContent = 'Copy & open Messenger';
        applicationResult.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        copyApplication.focus({ preventScroll: true });
    });

    copyApplication?.addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(applicationMessage.value);
            copyStatus.textContent = 'Copied. Open TCSO Messenger, paste the message and tap Send to submit.';
        } catch {
            applicationMessage.focus();
            applicationMessage.select();
            copyStatus.textContent = 'Select and copy this message, then paste it into TCSO Messenger and tap Send.';
        }
    });

    copyAndOpen?.addEventListener('click', async () => {
        const messengerTab = window.open('https://m.me/TCSODL', '_blank', 'noopener,noreferrer');
        try {
            await navigator.clipboard.writeText(applicationMessage.value);
            copyStatus.textContent = messengerTab
                ? 'Message copied. In the new Messenger tab, paste it into the TCSO chat and tap Send.'
                : 'Message copied, but your browser blocked the new tab. Tap “Open Messenger manually,” then paste and send.';
        } catch {
            applicationMessage.focus();
            applicationMessage.select();
            copyStatus.textContent = 'Clipboard access was blocked. The message is selected; copy it, open Messenger, paste and send.';
        }
    });
}
