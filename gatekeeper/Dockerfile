FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY . .
RUN go mod download
RUN CGO_ENABLED=0 go build -o gatekeeper main.go

FROM alpine:3.18
WORKDIR /app
COPY --from=builder /app/gatekeeper .
EXPOSE 9123
CMD ["./gatekeeper"]
