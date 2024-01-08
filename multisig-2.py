import smartpy as sp

@sp.module
def main():
    proposal_type:type = sp.big_map[
        sp.int, 
        sp.record(
            paymentAmt = sp.mutez, 
            receiver=sp.address, 
            voters = sp.set[sp.address],
            votingComplete = sp.bool
        )
    ]

    class MultiSigContract(sp.Contract):
        def __init__(self, members, requiredVotes):
            # Keep track of all the proposals submitted to the multisig
            self.data.proposals = sp.cast(sp.big_map(), proposal_type)
            self.data.activeProposalId = 0
            self.data.members = sp.cast(members, sp.set[sp.address])
            self.data.requiredVotes = sp.cast(requiredVotes, sp.nat)

        
        @sp.entrypoint
        def deposit(self):
            assert self.data.members.contains(sp.sender), 'Not a Member of MultiSig'

        @sp.entrypoint
        def submit_proposal(self, params):
            """
            Submit a new proposal/lambda for members
            of the MultiSig to vote for. 
            """ 
            assert self.data.members.contains(sp.sender), 'Not a Member of MultiSig'
            assert params.paymentAmt <= sp.balance, 'The MultiSig does not have enough funds for this proposal'
            self.data.activeProposalId += 1 # submitting a new proposal inactivates the last one
            self.data.proposals[self.data.activeProposalId]=sp.record(
                paymentAmt=params.paymentAmt, 
                receiver=params.receiver,
                voters=sp.set(sp.sender),
                votingComplete = False
            )
        
        @sp.entrypoint
        def vote_on_proposal(self):
            assert self.data.members.contains(sp.sender), 'Not a Member of MultiSig'
            # check if the user has previously voted on the proposal
            assert not self.data.proposals[self.data.activeProposalId].voters.contains(sp.sender), "Member has voted on this proposal"
            self.data.proposals[self.data.activeProposalId].voters.add(sp.sender)
            if sp.len(self.data.proposals[self.data.activeProposalId].voters) == self.data.requiredVotes:
                sp.send(self.data.proposals[self.data.activeProposalId].receiver, self.data.proposals[self.data.activeProposalId].paymentAmt)
                self.data.proposals[self.data.activeProposalId].votingComplete = True
                
                


@sp.add_test(name="Multisig")
def test():
    scenario = sp.test_scenario(main)
    alice = sp.address("tz1hGDfenyU6Ex6hVgUBhQzDAW7x2Ph3Rumj")
    bob = sp.address("tz1ayagi1KJN4Hfiu51CzBFTXuHabVhTUvzD")
    charlie = sp.address("tz1gTfzip6cEs6ZRc3MapBenz8iLJ7PkuE3b")
    dani = sp.test_account('dani')
    earl = sp.address("tz1eCsx5b9pSVyAxYDu7wUbR1qjqqwzQXvxn")
    
    scenario.h3("MultiSig Proposal Contract")
    members = sp.set([alice, bob, charlie, earl])

    contract = main.MultiSigContract(members, 3)
    scenario += contract

    scenario.h3("Members can add funds to the contract")
    contract.deposit().run(sender=alice, amount=sp.tez(50))

    scenario.h3("Members can submit a proposal for funds to be sent to an address - Proposal 1.")
    contract.submit_proposal(sp.record(paymentAmt=sp.tez(30), receiver=dani.address)).run(sender=alice)

    scenario.h3('Non-members cannot vote on proposals')
    contract.vote_on_proposal().run(valid=False, sender = dani.address)

    scenario.h3('Member 2 can vote on proposal')
    contract.vote_on_proposal().run(sender = bob)

    scenario.h3('Member 3 can vote on proposal')
    contract.vote_on_proposal().run(sender = charlie)

    scenario.h3('Contract balance should drop to 20tez after transfer')
    scenario.verify(contract.balance == sp.tez(20))

    scenario.h3("A New proposal can be created")
    contract.submit_proposal(sp.record(paymentAmt=sp.tez(20), receiver=dani.address)).run(sender=alice)

    scenario.h3("New proposal can be voted on")
    contract.vote_on_proposal().run(sender = charlie)

    
    
        





