import streamlit as st

st.set_page_config(page_title="TicketPilot", page_icon="🎫", layout="wide")

st.title("TicketPilot")
st.caption("Customer support triage • UI prototype only")

if "ticket" not in st.session_state:
    st.session_state.ticket = None
if "page" not in st.session_state:
    st.session_state.page = "Create Ticket"

with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Go to",
        ["Create Ticket", "Processing Pipeline"],
        index=0 if st.session_state.page == "Create Ticket" else 1,
    )
    st.session_state.page = page
    st.divider()
    st.caption("This version contains UI only. It does not call Jev, MCP tools, or an LLM.")

if st.session_state.page == "Create Ticket":
    st.header("Create a support ticket")
    st.write("Enter a real ticket to view it in the pipeline layout. Nothing is prefilled.")
    with st.form("ticket_form", clear_on_submit=False):
        subject = st.text_input("Subject *")
        customer_name = st.text_input("Customer name *")
        customer_email = st.text_input("Customer email (optional)")
        category = st.selectbox(
            "Reported category",
            ["Select a category", "Order issue", "Refund request", "Delivery delay",
             "Damaged item", "Account issue", "Billing issue", "Other"],
        )
        order_id = st.text_input("Order ID (optional)")
        amount = st.number_input("Order / refund amount (optional)", min_value=0.0, step=1.0)
        message = st.text_area("Customer message *", height=180)
        submitted = st.form_submit_button("Create ticket", type="primary")

    if submitted:
        if not subject.strip() or not customer_name.strip() or not message.strip():
            st.error("Please complete Subject, Customer name, and Customer message.")
        else:
            st.session_state.ticket = {
                "subject": subject.strip(),
                "customer_name": customer_name.strip(),
                "customer_email": customer_email.strip(),
                "category": category if category != "Select a category" else "Not specified",
                "order_id": order_id.strip(),
                "amount": amount,
                "message": message.strip(),
            }
            st.session_state.page = "Processing Pipeline"
            st.success("Ticket created in this session. Open Processing Pipeline in the sidebar.")
            st.rerun()

else:
    st.header("Processing pipeline")
    ticket = st.session_state.ticket
    if not ticket:
        st.info("No ticket has been created yet. Go to **Create Ticket** and enter one.")
    else:
        left, right = st.columns([1, 1])
        with left:
            st.subheader("Ticket details")
            st.markdown(f"**Subject:** {ticket['subject']}")
            st.markdown(f"**Customer:** {ticket['customer_name']}")
            st.markdown(f"**Email:** {ticket['customer_email'] or 'Not provided'}")
            st.markdown(f"**Category:** {ticket['category']}")
            st.markdown(f"**Order ID:** {ticket['order_id'] or 'Not provided'}")
            st.markdown(f"**Amount:** {ticket['amount']:.2f}" if ticket["amount"] else "**Amount:** Not provided")
            st.markdown("**Customer message**")
            st.write(ticket["message"])
        with right:
            st.subheader("Pipeline stages")
            stages = [
                ("1. Jev Review", "Placeholder only — classification and review are not connected."),
                ("2. MCP Tools", "Placeholder only — customer, order, and policy tools are not connected."),
                ("3. LLM Response", "Placeholder only — no response has been generated."),
                ("4. Final Safety Gate", "Placeholder only — safety checks and human approval are not connected."),
            ]
            for title, description in stages:
                with st.container(border=True):
                    st.markdown(f"### {title}")
                    st.caption(description)
                    st.info("Not run — integration not implemented.")
        st.divider()
        st.caption("Ticket data is stored only in Streamlit session state and is not saved to a database.")
        if st.button("Clear ticket", type="secondary"):
            st.session_state.ticket = None
            st.session_state.page = "Create Ticket"
            st.rerun()
