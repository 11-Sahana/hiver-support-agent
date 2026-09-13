# Intent Taxonomy (v1 — pending human review)

Derived from TF-IDF + KMeans (k=20) clustering of 8,000 customer-initiated
messages in the historical pool (`src/data/discover_intents.py`), then
merged/named by reading cluster samples. Clusters split largely by lexical
overlap, not true semantic meaning, so several clusters that were
conceptually the same issue (e.g. three different phrasings of "my package
is late") were merged by hand. All examples below are real, unedited
customer messages from the dataset.

**This is a v1 draft — flagging for your review before we use it to label
the golden set.** Things I'm least sure about are marked ⚠️ below.

---

### 1. ORDER_NOT_ARRIVED
**Definition:** Order/package has not arrived by the expected date; no
claim yet that tracking says "delivered."
**Examples:**
- "@AmazonHelp Hi can you check on my parcel that should of been here today before 8"
- "Amazon Prime's '2 day shipping' is a damn joke lmao. Where's my package??!"
**Do not use for:** tracking says delivered but customer says they never
got it → see `DELIVERED_BUT_NOT_RECEIVED`.
**Boundary:** a message with no urgency/complaint tone, just a status
check ("has my order shipped yet?") — still tag this intent; severity is a
separate signal, not a separate intent.

### 2. DELIVERED_BUT_NOT_RECEIVED
**Definition:** Tracking/notification says the order was delivered, but
the customer says they did not receive it.
**Examples:**
- "@115830 my order says it was delivered yesterday but we have received nothing 😢"
- "NOT MY DOOR MAT. NOT MY HOUSE. Where's my package?!?!"
**Do not use for:** order simply hasn't shipped/arrived yet with no
"delivered" claim → `ORDER_NOT_ARRIVED`.
**Boundary vs. PACKAGE_LOST:** if the customer or brand has already made
multiple failed attempts and used the word "lost," prefer `PACKAGE_LOST`.

### 3. PACKAGE_LOST
**Definition:** Package explicitly confirmed or described as lost — repeat
failures, carrier confirmation, or clear customer language ("lost my
package").
**Examples:**
- "Quitting Amazon. They've lost 3 packages in less than a week."
- "@AmazonHelp lost my lens and won't reimburse me for their mistake and neglect."
**Do not use for:** a single late/undelivered package with no "lost"
framing → `ORDER_NOT_ARRIVED` or `DELIVERED_BUT_NOT_RECEIVED`.
⚠️ **Boundary risk:** this intent overlaps heavily with #2; a labeler needs
a clear rule (e.g. "lost" = brand or customer treats the package as
unrecoverable, not just late) — worth pressure-testing on real boundary
cases during golden-set labeling.

### 4. WRONG_OR_DAMAGED_ITEM
**Definition:** Item received is wrong, broken, defective, or arrived in
damaged packaging.
**Examples:**
- "product delivered way too late, damaged, picked up earlier than scheduled"
- "Amazon sent the wrong cases"
**Do not use for:** the item hasn't arrived at all → delivery intents above.

### 5. RETURN_OR_EXCHANGE_REQUEST
**Definition:** Customer wants to return/exchange an item, or is asking
about the return process, label, or pickup.
**Examples:**
- "I tried placing an order... and would like to return the same item."
- "Is there any way to return a product if you don't have a printer to print the label out?"
**Boundary vs. REFUND_STATUS:** if the ask is specifically about money
coming back rather than the physical item process, prefer `REFUND_STATUS`.

### 6. REFUND_STATUS
**Definition:** A refund was promised/initiated but not received, or
there's a dispute about the refund amount.
**Examples:**
- "Refund not received but your message received me shows that refund was success on my visa card"
- "Stole Rs. 1862 from me - I have neither received my order, Amazon is lying that they delivered, not giving refund"

### 7. ORDER_CANCELLATION
**Definition:** An order was cancelled unexpectedly (by Amazon/seller), or
the customer wants to cancel an order/pre-order.
**Examples:**
- "Order canceled. Paid using Amazon Pay. Refund not issued. WHY???"
- "@AmazonHelp @115850 Order ID- ... picked up with wrong tracking details, please help!" ⚠️ borderline — mixes tracking + possible cancellation

### 8. PRIME_MEMBERSHIP_BILLING
**Definition:** Unwanted Prime renewal charge, free-trial cancellation, or
a dispute about the membership charge itself (not a general payment
method problem).
**Examples:**
- "@AmazonHelp how do i cancel my free trial with amazon prime? I have a fire stick :)"
- "Y'all Amazon prime just charged me $99 because i forgot my 30 days was up."

### 9. PAYMENT_OR_CHARGE_ISSUE
**Definition:** Amazon Pay balance/payment failures, being double-charged,
or other payment-method problems not specific to a Prime subscription.
**Examples:**
- "its been almost 45 mins since I added money on my Amazon Pay. But Amazon Pay is not showing the amount."
- "@AmazonHelp u guys charged me $84 for an item twice."
**Boundary vs. PRIME_MEMBERSHIP_BILLING:** if "Prime" or "membership" is
the specific subject of the charge, use that intent instead.

### 10. ACCOUNT_ACCESS_SECURITY
**Definition:** Locked out of account, suspected hacking, unauthorized
account activity, or password-reset failure.
**Examples:**
- "@AmazonHelp I can't sign on to my account. When I ask for a password reset no email comes with a code. Help!!"
- "@AmazonHelp Hey, I found what seems to be a pretty serious security flaw in your new sign-in page..."
**Escalation note (Phase 12 preview):** this category is a strong
candidate for "never auto-handle" — account security missteps are
high-risk regardless of model confidence.

### 11. PRODUCT_USAGE_QUESTION
**Definition:** A how-to or feature question about a device/service
(Alexa, Echo, Kindle, Prime Video app), not a complaint about a failure.
**Examples:**
- "@115833 Honestly, I'm offended. Maybe it's time for Google Home? #alexa #googlehome" ⚠️ borderline — could be a joke, not a real question; flagged as a labeling difficulty
- "@AmazonHelp What does the #NewEchoPlus do for me that the #NewEcho or the #Echo1stGen does not?"

### 12. GENERAL_COMPLAINT_OTHER
**Definition:** Venting, general dissatisfaction, or a complaint with no
specific, actionable resolution request — or anything not covered above.
This is the catch-all/OTHER bucket the assignment calls for.
**Examples:**
- "@115821 as usual another broken promise from Amazon, customer service leaves a lot to be desired!"
- "Service u receive as an Amazon Prime customer is awful."
**Note:** by definition this intent has no clear "resolution" to retrieve
— it's a strong candidate for escalation (or a polite acknowledgment
reply) rather than an attempted fix, since there's no concrete ask to
satisfy.

---

## What's still uncertain (flagging honestly, not hiding it)

- 12 intents, within the 8-15 target range, but **not yet validated against
  a labeled sample** — the boundary cases marked ⚠️ above are real risks
  for inter-label confusion once we build the golden set.
- TF-IDF clustering surfaces lexical patterns, not semantic ones — it's
  quite possible a genuinely embedding-based clustering pass would merge
  or split some of these differently. Noted as a limitation in the
  decision log rather than pretending this taxonomy is definitive.
- `GENERAL_COMPLAINT_OTHER` risks becoming a dumping ground if labelers
  default to it whenever unsure — worth watching for during golden-set
  labeling and tightening the boundary if it's overused.

## Next step

Please review this taxonomy — merge/split/rename anything that doesn't
match your read of the data — before I move to Phase 5 (golden set), since
the golden set labels will be built against whatever taxonomy we lock here.
