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
    const emailInput = document.querySelector('#applicant-contact');
    const emailStatus = document.querySelector('#email-status');
    const sendCode = document.querySelector('#send-code');
    const verifyCode = document.querySelector('#verify-code');
    const otpEntry = document.querySelector('#otp-entry');
    const codeInput = document.querySelector('#email-code');
    let verificationToken = '', verifiedEmail = '', challenge = '', verificationExpires = 0, resendUntil = 0, emailBusy = false;
    const api = async (path, body) => {
        const response = await fetch(`https://myotaw.com/tcso-api/${path}`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:AbortSignal.timeout(20000)});
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Please try again.');
        return data;
    };
    const emailIsVerified = () => verificationToken && verifiedEmail === emailInput.value.trim().toLowerCase() && Date.now() < verificationExpires;
    const resetVerification = () => {
        verificationToken = ''; verifiedEmail = ''; challenge = ''; verificationExpires = 0;
        otpEntry.hidden = true; codeInput.value = ''; emailStatus.textContent = 'Email verification is required before submission.';
        emailStatus.classList.remove('is-verified'); sendCode.hidden = false;
    };
    emailInput.addEventListener('input', resetVerification);
    sendCode.addEventListener('click', async () => {
        if (emailBusy || Date.now() < resendUntil || !emailInput.reportValidity()) return;
        if (!document.querySelector('#email-consent').checked) {
            emailStatus.textContent = 'Please agree to receive the verification email first.';
            document.querySelector('#email-consent').focus(); return;
        }
        emailBusy = true; sendCode.disabled = true; emailInput.readOnly = true;
        emailStatus.textContent = 'Sending your verification code…';
        try {
            const data = await api('otp/request', {email:emailInput.value.trim(), email_consent:true,website:membershipForm.elements.website.value});
            challenge = data.challenge_id; verificationToken = ''; verifiedEmail = '';
            resendUntil = Date.now() + data.resend_after * 1000; otpEntry.hidden = false;
            emailStatus.textContent = `Code sent to ${emailInput.value.trim()}. Enter the six digits below.`;
            codeInput.value = ''; codeInput.focus();
        } catch(error) { emailStatus.textContent = error.name === 'TimeoutError' ? 'Sending timed out. Check your inbox before requesting another code.' : error.message; }
        finally { emailBusy = false; emailInput.readOnly = false; sendCode.disabled = Date.now() < resendUntil; }
    });
    setInterval(() => {
        const remaining = Math.max(0,Math.ceil((resendUntil-Date.now())/1000));
        sendCode.textContent = remaining ? `Resend code in ${remaining}s` : challenge ? 'Resend verification code' : 'Send verification code';
        sendCode.disabled = emailBusy || remaining > 0;
    },1000);
    verifyCode.addEventListener('click', async () => {
        if (emailBusy || !challenge) return;
        if (!/^\d{6}$/.test(codeInput.value.trim())) { emailStatus.textContent = 'Enter the six-digit code from your email.'; codeInput.focus(); return; }
        emailBusy = true; verifyCode.disabled = true; emailInput.readOnly = true;
        emailStatus.textContent = 'Checking your code…';
        try {
            const data = await api('otp/verify',{email:emailInput.value.trim(),challenge_id:challenge,code:codeInput.value.trim()});
            verificationToken = data.verification_token; verifiedEmail = emailInput.value.trim().toLowerCase(); verificationExpires = Date.now()+data.expires_in*1000;
            codeInput.value = ''; otpEntry.hidden = true; sendCode.hidden = true;
            emailStatus.textContent = `✓ Email verified: ${verifiedEmail}. You can now review your application.`; emailStatus.classList.add('is-verified');
            document.querySelector('.form-submit').focus();
        } catch(error) { emailStatus.textContent = error.message; }
        finally { emailBusy = false; verifyCode.disabled = false; emailInput.readOnly = false; }
    });
    codeInput.addEventListener('keydown', event => { if(event.key==='Enter') {event.preventDefault();verifyCode.click();} });
    const countryInput = document.querySelector('#applicant-country');
    const countryOptions = document.querySelector('#country-options');
    const regionNames = new Intl.DisplayNames(['en'], {type:'region'});
    const regionCodes = 'AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ BA BB BD BE BF BG BH BI BJ BL BM BN BO BQ BR BS BT BV BW BY BZ CA CC CD CF CG CH CI CK CL CM CN CO CR CU CV CW CX CY CZ DE DJ DK DM DO DZ EC EE EG EH ER ES ET FI FJ FK FM FO FR GA GB GD GE GF GG GH GI GL GM GN GP GQ GR GS GT GU GW GY HK HM HN HR HT HU ID IE IL IM IN IO IQ IR IS IT JE JM JO JP KE KG KH KI KM KN KP KR KW KY KZ LA LB LC LI LK LR LS LT LU LV LY MA MC MD ME MF MG MH MK ML MN MO MP MQ MR MS MT MU MV MW MX MY MZ NA NC NE NF NG NI NL NO NP NR NU NZ OM PA PE PF PG PH PK PL PM PN PR PS PT PW PY QA RE RO RS RU RW SA SB SC SD SE SG SH SI SJ SK SL SM SN SO SR SS ST SV SX SY SZ TC TD TF TG TH TJ TK TL TM TN TO TR TT TV TW TZ UA UG UM US UY UZ VA VC VE VG VI VN VU WF WS YE YT ZA ZM ZW'.split(' ');
    const countries = regionCodes.map(code=>({code,name:regionNames.of(code)}));
    const popular = ['TH','SG','JP','US','GB','AU','CA','MY','KR','DE'];
    let matches = [], activeCountry = -1;
    const closeCountries = () => {countryOptions.hidden=true;countryInput.setAttribute('aria-expanded','false');countryInput.removeAttribute('aria-activedescendant');activeCountry=-1;};
    const pickCountry = index => {
        if(!matches[index])return;
        countryInput.value=matches[index].name;countryInput.setCustomValidity('');closeCountries();countryInput.focus();invalidate();
    };
    const showCountries = () => {
        const query=countryInput.value.trim().toLowerCase();
        matches=countries.filter(c=>!query || c.name.toLowerCase().includes(query) || c.code.toLowerCase()===query || (c.code==='US' && ['usa','america'].includes(query)) || (c.code==='GB' && ['uk','england','britain'].includes(query)))
            .sort((a,b)=>query ? Number(!a.name.toLowerCase().startsWith(query))-Number(!b.name.toLowerCase().startsWith(query)) || a.name.localeCompare(b.name) : (popular.includes(a.code)?popular.indexOf(a.code):99)-(popular.includes(b.code)?popular.indexOf(b.code):99)||a.name.localeCompare(b.name));
        countryOptions.replaceChildren();activeCountry=-1;
        matches.forEach((country,index)=>{const item=document.createElement('li');item.id=`country-option-${country.code}`;item.setAttribute('role','option');item.setAttribute('aria-selected','false');item.textContent=country.name;item.addEventListener('pointerdown',e=>{e.preventDefault();pickCountry(index);});countryOptions.append(item);});
        if(!matches.length){const item=document.createElement('li');item.textContent='No country found. Try another spelling.';countryOptions.append(item);}
        countryOptions.hidden=false;countryInput.setAttribute('aria-expanded','true');
    };
    countryInput.addEventListener('focus',showCountries);
    countryInput.addEventListener('input',()=>{countryInput.setCustomValidity('');showCountries();});
    countryInput.addEventListener('blur',()=>{closeCountries();if(countryInput.value && !countries.some(c=>c.name===countryInput.value))countryInput.setCustomValidity('Choose a country from the search results.');});
    countryInput.addEventListener('keydown',event=>{
        if(event.key==='Escape'){closeCountries();return;}
        if(event.key==='Enter' && !countryOptions.hidden){event.preventDefault();pickCountry(activeCountry<0?0:activeCountry);return;}
        if(['ArrowDown','ArrowUp'].includes(event.key)){
            event.preventDefault();if(countryOptions.hidden)showCountries();
            if(!matches.length)return;
            activeCountry=Math.max(0,Math.min(matches.length-1,activeCountry+(event.key==='ArrowDown'?1:-1)));
            [...countryOptions.children].forEach((item,index)=>item.setAttribute('aria-selected',String(index===activeCountry)));
            const selected=countryOptions.children[activeCountry];countryInput.setAttribute('aria-activedescendant',selected.id);selected.scrollIntoView({block:'nearest'});
        }
    });

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
        if (!emailIsVerified()) { emailStatus.textContent = 'Verify your email before reviewing your application.'; emailInput.focus(); return; }
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
            `Follow-up email: ${fields.contact} (verified)`,
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
        message.style.height = 'auto';
        message.style.height = `${message.scrollHeight + 4}px`;
        copyStatus.textContent = '';
        submitStatus.textContent = 'Preview ready. Your application has not been sent yet.';
        submitStatus.classList.remove('is-error');
        result.scrollIntoView({behavior: 'smooth', block: 'start'});
        consent.focus({preventScroll:true});
    });
    submitButton.addEventListener('click', async () => {
        if (!payload || submitting || submitted) return;
        if (!emailIsVerified()) { submitStatus.textContent = 'Your email verification expired. Verify again before submitting.'; resetVerification(); emailInput.focus(); return; }
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
                body: JSON.stringify({...payload, consent:true, verification_token:verificationToken}), signal: AbortSignal.timeout(15000)
            });
            const data = await response.json();
            if (!response.ok || !data.reference) throw new Error(data.error || 'Submission could not be confirmed.');
            submitted = true;
            message.value = `TCSO application reference: ${data.reference}\nSaved online; following up in Messenger.\n\n${message.value}`;
            message.style.height = `${message.scrollHeight + 4}px`;
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
