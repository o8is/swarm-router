package main

import (
	"log"
	"net/http"
	"os"

	dnslink "github.com/dnslink-std/go"
)

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "9123"
	}

	http.HandleFunc("/check", func(w http.ResponseWriter, r *http.Request) {
		domain := r.URL.Query().Get("domain")
		if domain == "" {
			http.Error(w, "domain required", http.StatusBadRequest)
			return
		}

		// 1. Basic Security Check: Does it have a DNSLink?
		// This prevents us from issuing certs for domains that don't even point to us.
		link, err := dnslink.Resolve(domain)
		if err != nil {
			log.Printf("[Deny] %s: No valid DNSLink (%v)", domain, err)
			w.WriteHeader(http.StatusForbidden)
			return
		}

		// 2. (Future) Revenue Check: Is the domain registered in our smart contract?
		// if !checkSmartContract(domain) {
		//     w.WriteHeader(http.StatusPaymentRequired)
		//     return
		// }

		// Find a link
		var linkStr string
		for namespace, entries := range link.Links {
			if len(entries) > 0 {
				linkStr = "/" + namespace + "/" + entries[0].Identifier
				break
			}
		}

		if linkStr == "" {
			log.Printf("[Deny] %s: No valid DNSLink found in result", domain)
			w.WriteHeader(http.StatusForbidden)
			return
		}

		log.Printf("[Allow] %s: Found %s", domain, linkStr)
		w.WriteHeader(http.StatusOK)
	})

	log.Printf("Gatekeeper listening on :%s", port)
	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatal(err)
	}
}
